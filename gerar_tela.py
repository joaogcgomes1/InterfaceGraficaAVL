"""
Arcball
"""

import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QSurfaceFormat
from ler_avl import ler_AVL

CUSTOM_AXES = [
    ("X", (0.0, 0.0, 1.0), (1.0, 0.2, 0.2), QColor(255, 100, 100)),
    ("Y", (-1.0, 0.0,  0.0), (0.2, 1.0, 0.2), QColor(100, 255, 100)),
    ("Z", (0.0, 1.0,  0.0), (0.3, 0.5, 1.0), QColor(100, 150, 255))
]

def quat_from_axis_angle(axis, angle_deg):
    angle = math.radians(angle_deg)
    axis = np.array(axis, dtype=np.float32)
    axis /= np.linalg.norm(axis)
    s = math.sin(angle / 2.0)
    return np.array([math.cos(angle / 2.0), axis[0]*s, axis[1]*s, axis[2]*s], dtype=np.float32)

class Arcball:
    def __init__(self):
        self.q_now   = np.array([1.0, 0.0, 0.0, 0.0])
        self.q_drag  = np.array([1.0, 0.0, 0.0, 0.0])
        self.v_start = np.array([0.0, 0.0, 1.0])
        self.dragging = False

    @staticmethod
    def _quat_mul(q1, q2):
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        return np.array([
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2,
        ])

    @staticmethod
    def _quat_to_matrix(q):
        w, x, y, z = q / np.linalg.norm(q)
        return np.array([
            [1-2*(y*y+z*z),   2*(x*y-z*w),   2*(x*z+y*w), 0],
            [  2*(x*y+z*w), 1-2*(x*x+z*z),   2*(y*z-x*w), 0],
            [  2*(x*z-y*w),   2*(y*z+x*w), 1-2*(x*x+y*y), 0],
            [           0,             0,             0,    1],
        ], dtype=np.float32)

    def _screen_to_sphere(self, sx, sy, width, height):
        x =  (2.0 * sx / width  - 1.0)
        y = -(2.0 * sy / height - 1.0)
        r2 = x*x + y*y
        if r2 <= 1.0: return np.array([x, y, math.sqrt(1.0 - r2)])
        n = math.sqrt(r2)
        return np.array([x/n, y/n, 0.0])

    def begin_drag(self, sx, sy, width, height):
        self.v_start = self._screen_to_sphere(sx, sy, width, height)
        self.q_drag  = np.array([1.0, 0.0, 0.0, 0.0])
        self.dragging = True

    def update_drag(self, sx, sy, width, height):
        if not self.dragging: return
        v_end = self._screen_to_sphere(sx, sy, width, height)
        axis  = np.cross(self.v_start, v_end)
        dot   = float(np.clip(np.dot(self.v_start, v_end), -1.0, 1.0))
        angle = math.acos(dot)
        n = np.linalg.norm(axis)
        if n < 1e-8 or abs(angle) < 1e-8:
            self.q_drag = np.array([1.0, 0.0, 0.0, 0.0])
            return
        axis /= n
        s = math.sin(angle / 2.0)
        self.q_drag = np.array([math.cos(angle / 2.0), axis[0]*s, axis[1]*s, axis[2]*s])

    def end_drag(self):
        self.q_now    = self._quat_mul(self.q_drag, self.q_now)
        self.q_drag   = np.array([1.0, 0.0, 0.0, 0.0])
        self.dragging = False

    def get_matrix(self):
        return self._quat_to_matrix(self._quat_mul(self.q_drag, self.q_now))

    def reset(self):
        self.q_now = self.q_drag = np.array([1.0, 0.0, 0.0, 0.0])
        self.dragging = False

def make_airplane(filename):
    aeronave = ler_AVL(filename)
    if not aeronave: return np.array([]), [], False

    verts, faces_out = [], []
    cor_fixa, cor_movel = (0.25, 0.45, 0.75), (0, 0, 1)

    def add_panel(sec1, sec2, color, mirror=False, ctrl_h1=None, ctrl_h2=None, ctrl_color=None):
        def build_surface(s1, s2, is_mirrored=False):
            def get_coord(s, frac): return [s[1], s[2], s[0] + s[3] * frac]

            def make_quad(pt0, pt1, pt2, pt3, face_color):
                base_idx = len(verts)
                p0, p1, p2, p3 = map(np.array, (pt0, pt1, pt2, pt3))
                
                # 1. Calcula a normal 
                norm_top = np.cross(p1 - p0, p2 - p0)
                if np.linalg.norm(norm_top) > 1e-8: 
                    norm_top = norm_top / np.linalg.norm(norm_top)
                else: 
                    norm_top = np.array([0.0, 1.0, 0.0])
                
                # 2. SE FOR ESPELHADO, a normal deve ser invertida para olhar para fora
                if is_mirrored:
                    norm_top = -norm_top
                
                
                mo = norm_top * 0.005
                verts.extend((p + mo).tolist() for p in (p0, p1, p2, p3))
                verts.extend((p - mo).tolist() for p in (p0, p1, p2, p3))

                # 4. Ordem de desenho
                ft, fb = [0, 1, 2, 3], [7, 6, 5, 4]
                if is_mirrored: 
                    ft, fb = ft[::-1], fb[::-1]

                # 5. Salva as faces com suas normais definitivas
                faces_out.append(([i + base_idx for i in ft], norm_top.tolist(), face_color))
                faces_out.append(([i + base_idx for i in fb], (-norm_top).tolist(), face_color))

            if ctrl_h1 is not None and ctrl_h2 is not None:
                make_quad(get_coord(s1, 0.0), get_coord(s1, ctrl_h1), get_coord(s2, ctrl_h2), get_coord(s2, 0.0), color)
                make_quad(get_coord(s1, ctrl_h1), get_coord(s1, 1.0), get_coord(s2, 1.0), get_coord(s2, ctrl_h2), ctrl_color)
            else:
                make_quad(get_coord(s1, 0.0), get_coord(s1, 1.0), get_coord(s2, 1.0), get_coord(s2, 0.0), color)

        build_surface(sec1, sec2)
        if mirror: build_surface((sec1[0], -sec1[1], sec1[2], sec1[3]), (sec2[0], -sec2[1], sec2[2], sec2[3]), True)

    for sup in aeronave["superficies"]:
        dx, dy, dz = sup.get("translate", [0.0, 0.0, 0.0])
        mirror = sup.get("yduplicate") is not None
        secoes = sup.get("secoes", [])
        
        for i in range(len(secoes) - 1):
            sec1, sec2 = secoes[i], secoes[i + 1]
            s1_tuple = (sec1["x"]+dx, sec1["y"]+dy, sec1["z"]+dz, sec1["corda"])
            s2_tuple = (sec2["x"]+dx, sec2["y"]+dy, sec2["z"]+dz, sec2["corda"])

            c_h1 = c_h2 = c_col = None
            if sec1.get("controles") and sec2.get("controles"):
                for c1 in sec1["controles"]:
                    c2 = next((c for c in sec2["controles"] if c["nome"] == c1["nome"]), None)
                    if c2: c_h1, c_h2, c_col = c1["hinge"], c2["hinge"], cor_movel; break
            
            add_panel(s1_tuple, s2_tuple, cor_fixa, mirror, c_h1, c_h2, c_col)

    return np.array(verts, dtype=np.float32), faces_out, aeronave.get("nome", "Avião")

class Viewer3D(QOpenGLWidget):
    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.filename = filename
        
        
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.arcball = Arcball()
        self.zoom = -12.75
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.wireframe = False
        
        # Rotação inicial
        qx = quat_from_axis_angle((1,0,0), 25)
        qy = quat_from_axis_angle((0,1,0), 45)
        self.arcball.q_now = Arcball._quat_mul(qx, qy)
        
        self.last_pos = QPoint()
        self.is_panning = False
        self.is_rotating = False

        # Geometria
        self.verts, self.faces, self.geo_name = make_airplane(self.filename)
        self.centroide = np.mean(self.verts, axis=0) if len(self.verts) > 0 else np.array([0.0, 0.0, 0.0])
        
        self.font_hud = QFont("Monospace", 10)
        self.font_axes = QFont("Monospace", 9, QFont.Bold)

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        
        # --- Configurações de Iluminação ---
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE) 
        glEnable(GL_NORMALIZE) 
        
        # Suavização (Multisampling)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_LINE_SMOOTH)

        glLightfv(GL_LIGHT0, GL_POSITION, [3, 5, 4, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [0.9, 0.9, 0.9, 1])
      
        glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.4, 0.4, 0.4, 1]) 
        
        glLightfv(GL_LIGHT1, GL_POSITION, [-3,-2,-3, 1])
        glLightfv(GL_LIGHT1, GL_DIFFUSE,  [0.3, 0.3, 0.5, 1])

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if h > 0: gluPerspective(45, w/h,1, 100)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        # 1. RENDERIZAÇÃO 3D (PyOpenGL)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE) 
        glClearColor(0.08, 0.08, 0.12, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glLoadIdentity()
        glTranslatef(self.pan_x, self.pan_y, self.zoom)
        rot = self.arcball.get_matrix()
        glMultMatrixf(rot.T)
        glTranslatef(-self.centroide[0], -self.centroide[1], -self.centroide[2])
        
        self.draw_grid()
        self.draw_axes_lines()
        self.draw_geometry()

        
        model_mat = glGetDoublev(GL_MODELVIEW_MATRIX)
        proj_mat = glGetDoublev(GL_PROJECTION_MATRIX)
        view_mat = glGetIntegerv(GL_VIEWPORT)

        # 2. RENDERIZAÇÃO 2D 
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Desenha os números dos eixos 
        painter.setFont(self.font_axes)
        self.draw_axes_labels(painter, model_mat, proj_mat, view_mat)
        
        # Desenha o HUD
        painter.setFont(self.font_hud)
        painter.setPen(QColor(200, 220, 255))
        
        hud_lines = [
            f"Geometria: {self.geo_name}",
            f"[W] Wireframe: {'ON' if self.wireframe else 'OFF'}    [R] Reset",
            "Arraste (LMB) = rotaciona | Scroll = zoom | Arraste (RMB) = pan",
            "Vistas: [1] Frontal  [2] Lateral  [3] Superior  [4] Traseira"
        ]
        y_offset = self.height() - (len(hud_lines) * 20)
        for i, line in enumerate(hud_lines):
            painter.drawText(15, y_offset + (i * 20), line)
            
        painter.end()

    # --- Desenhos 3D ---
    def draw_grid(self):
        glDisable(GL_LIGHTING)
        glColor4f(0.5, 0.5, 0.5, 0.15)
        glBegin(GL_LINES)
        for i in range(-30, 31):
            glVertex3f(i, -2, -30); glVertex3f(i, -2, 30)
            glVertex3f(-30, -2, i); glVertex3f(30, -2, i)
        glEnd()
        glEnable(GL_LIGHTING)

    def draw_axes_lines(self):
        glDisable(GL_LIGHTING)
        glLineWidth(2)
        for name, vec, gl_color, txt_color in CUSTOM_AXES:
            projeções = np.dot(self.verts, vec) if len(self.verts) > 0 else [0]
            limit = max(np.max(np.abs(projeções)) * 1.5, 1.0)
            passo = 0.5 if limit <= 2.0 else (1.0 if limit <= 5.0 else 2.0)
            valores = np.concatenate([-np.arange(passo, limit, passo)[::-1], np.arange(passo, limit, passo)])

            v_arr = np.array(vec)
            ref = np.array([0.0, 1.0, 0.0]) if abs(v_arr[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
            perp = np.cross(v_arr, ref)
            if np.linalg.norm(perp) > 1e-8: perp = perp / np.linalg.norm(perp)
            
            glBegin(GL_LINES)
            glColor3fv(gl_color)
            glVertex3f(-vec[0] * limit, -vec[1] * limit, -vec[2] * limit)
            glVertex3f( vec[0] * limit,  vec[1] * limit,  vec[2] * limit)
            
            tamanho_traco = 0.05
            for val in valores:
                cx, cy, cz = vec[0]*val, vec[1]*val, vec[2]*val
                glVertex3f(cx - perp[0]*tamanho_traco, cy - perp[1]*tamanho_traco, cz - perp[2]*tamanho_traco)
                glVertex3f(cx + perp[0]*tamanho_traco, cy + perp[1]*tamanho_traco, cz + perp[2]*tamanho_traco)
            glEnd()
        glLineWidth(1)
        glEnable(GL_LIGHTING)

    def draw_geometry(self):
        if self.wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glColor3f(0.2, 0.8, 0.2)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        for face in self.faces:
            if len(face) == 3 and isinstance(face[0], list): idx_list, norm, col = face
            else: idx_list, norm, col = face[0], face[1], None

            glNormal3fv(norm)
            if col and not self.wireframe: glColor3fv(col)
            elif not self.wireframe: glColor3f(0.7, 0.7, 0.9)

            glBegin(GL_TRIANGLES if len(idx_list) == 3 else GL_QUADS)
            for i in idx_list: glVertex3fv(self.verts[i])
            glEnd()
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    # --- Desenhos 2D (Overlay) ---
    def draw_axes_labels(self, painter, model, proj, view):
        for name, vec, gl_color, txt_color in CUSTOM_AXES:
            projeções = np.dot(self.verts, vec) if len(self.verts) > 0 else [0]
            limit = max(np.max(np.abs(projeções)) * 1.5, 1.0)
            passo = 0.5 if limit <= 2.0 else (1.0 if limit <= 5.0 else 2.0)
            valores = np.concatenate([-np.arange(passo, limit, passo)[::-1], np.arange(passo, limit, passo)])

            v_arr = np.array(vec)
            ref = np.array([0.0, 1.0, 0.0]) if abs(v_arr[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
            perp = np.cross(v_arr, ref)
            if np.linalg.norm(perp) > 1e-8: perp = perp / np.linalg.norm(perp)

            painter.setPen(txt_color)
            
            # Posição da letra do eixo na ponta
            try:
                wx, wy, wz = gluProject(vec[0]*limit*1.1, vec[1]*limit*1.1, vec[2]*limit*1.1, model, proj, view)
                if wz < 1.0: painter.drawText(int(wx), int(view[3] - wy), name)
            except: pass

            afastamento = 0.15
            for val in valores:
                val_str = f"{val:.1f}" if val % 1 != 0 else f"{int(val)}"
                px, py, pz = vec[0]*val + perp[0]*afastamento, vec[1]*val + perp[1]*afastamento, vec[2]*val + perp[2]*afastamento
                try:
                    wx, wy, wz = gluProject(px, py, pz, model, proj, view)
                    if wz < 1.0: painter.drawText(int(wx), int(view[3] - wy), val_str)
                except: pass

    # --- Eventos de Input---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_rotating = True
            self.arcball.begin_drag(event.x(), event.y(), self.width(), self.height())
        elif event.button() == Qt.RightButton:
            self.is_panning = True
            self.last_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_rotating = False
            self.arcball.end_drag()
        elif event.button() == Qt.RightButton:
            self.is_panning = False

    def mouseMoveEvent(self, event):
        if self.is_rotating:
            self.arcball.update_drag(event.x(), event.y(), self.width(), self.height())
            self.update()
        elif self.is_panning:
            dx = event.x() - self.last_pos.x()
            dy = event.y() - self.last_pos.y()
            self.pan_x += dx * 0.01
            self.pan_y -= dy * 0.01
            self.last_pos = event.pos()
            self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0: self.zoom += 0.5
        else: self.zoom -= 0.5
        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_R, Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4):
            self.zoom = -14
            self.arcball.reset()
            if key == Qt.Key_R: self.arcball.q_now = Arcball._quat_mul(quat_from_axis_angle((1, 0, 0), 25), quat_from_axis_angle((0, 1, 0), 45))
            elif key == Qt.Key_1: self.arcball.q_now = quat_from_axis_angle((0, 1, 0), 180)
            elif key == Qt.Key_2: self.arcball.q_now = quat_from_axis_angle((0, 1, 0), -90)
            elif key == Qt.Key_3: self.arcball.q_now = quat_from_axis_angle((1, 0, 0), 90)
            elif key == Qt.Key_4: self.arcball.q_now = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)

            rot_matrix = Arcball._quat_to_matrix(self.arcball.q_now)
            v_desloc = np.dot(rot_matrix, [-self.centroide[0], -self.centroide[1], -self.centroide[2], 1.0])
            self.pan_x, self.pan_y = -v_desloc[0], -v_desloc[1]
            
        elif key == Qt.Key_W:
            self.wireframe = not self.wireframe
            
        self.update()
