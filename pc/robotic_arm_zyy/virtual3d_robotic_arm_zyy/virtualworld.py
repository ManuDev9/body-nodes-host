#
# MIT License
# 
# Copyright (c) 2025 Manuel Bottini
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Virtual 3d Environment
import pygame

from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *


# Slider class for handling input and rendering
class HorizontalSlider:
    def __init__(self, label, viewport, x, y, width, min_val, max_val, initial_val=None, height=20):
        self.label = label
        self.viewport = viewport
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val if initial_val is not None else (min_val + max_val) / 2
        self.dragging = False
        self.mouse_down = False
        self.handle_width = 10  # Width of slider knob

    def value_to_pos(self):
        """Map the current value to an x position on the slider."""
        t = (self.value - self.min_val) / (self.max_val - self.min_val)
        return self.x + t * (self.width - self.handle_width)

    def pos_to_value(self, px):
        """Map a mouse x position to a value."""
        t = (px - self.x) / (self.width - self.handle_width)
        t = max(0.0, min(1.0, t))  # Clamp
        return self.min_val + t * (self.max_val - self.min_val)

    def draw(self):

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, self.viewport["size"][0], 0, self.viewport["size"][1])

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)

        # Draw track
        glColor3f(0.6, 0.6, 0.6)
        glBegin(GL_QUADS)
        glVertex2f(self.x, self.y + self.height / 3)
        glVertex2f(self.x + self.width, self.y + self.height / 3)
        glVertex2f(self.x + self.width, self.y + 2 * self.height / 3)
        glVertex2f(self.x, self.y + 2 * self.height / 3)
        glEnd()

        # Draw handle
        handle_x = self.value_to_pos()
        glColor3f(1.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(handle_x, self.y)
        glVertex2f(handle_x + self.handle_width, self.y)
        glVertex2f(handle_x + self.handle_width, self.y + self.height)
        glVertex2f(handle_x, self.y + self.height)
        glEnd()

        # Draw label
        text_x = self.x + self.width / 2 - len(self.label) * 3
        text_y = self.y + self.height / 2 - 4
        glColor3f(0.0, 0.2, 1.0)
        glRasterPos2f(text_x, text_y)
        for ch in self.label:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

        # Restore OpenGL state
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

    def handle_event(self, event):

        if event.type == MOUSEBUTTONDOWN:
            self.mouse_down = True
        elif event.type == MOUSEBUTTONUP:
            self.mouse_down = False


        mx, my = pygame.mouse.get_pos()
        mx = mx - self.viewport["start"][0]
        my = self.viewport["size"][1] - my + self.viewport["start"][1]  # Flip Y for OpenGL

        handle_x = self.value_to_pos()
        if self.mouse_down:
            if (handle_x <= mx <= handle_x + self.handle_width and
                self.y <= my <= self.y + self.height):
                self.dragging = True

        if not self.mouse_down:
            self.dragging = False

        if self.dragging:
            self.value = self.pos_to_value(mx)

    def get_value(self):
        return self.value


def setOrthoProjection(virt3d, viewport):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    aspect = virt3d["camera"]["display"][0] / virt3d["camera"]["display"][1]
    scale = viewport["slider"]["zoom"].get_value()
    glOrtho(-scale * aspect, scale * aspect, -scale, scale, -1000, 1000)

    gluLookAt(
        viewport["slider"]["eyeX"].get_value(),
        viewport["slider"]["eyeY"].get_value(),
        viewport["slider"]["eyeZ"].get_value(),
        0, 0, 0,           # Look at 0,0,0
        0, 0, 1            # Up vector
    )

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def setupVirtual3dEnvironment():
    virt3d = {}

    print("Initializing virtual world for Bodynodes sensors")

    # Camera
    virt3d["camera"] = {}
    virt3d["camera"]["display"] = (800, 600)

    virt3d["viewport"] = [{}] # One viewport
    virt3d["viewport"][0]["start"] = (0, 0)
    virt3d["viewport"][0]["size"] = (virt3d["camera"]["display"][0], 600)
    virt3d["viewport"][0]["slider"] = {}
    virt3d["viewport"][0]["slider"]["zoom"] = HorizontalSlider(label="Zoom0",viewport=virt3d["viewport"][0], x=50, y=570, width=300, min_val=1.0, max_val=10.0, initial_val=4.5, height=20)
    virt3d["viewport"][0]["slider"]["eyeX"] = HorizontalSlider(label="EyeX0",viewport=virt3d["viewport"][0], x=50, y=540, width=300, min_val=-20.0, max_val=20.0, initial_val=8.0, height=20)
    virt3d["viewport"][0]["slider"]["eyeY"] = HorizontalSlider(label="EyeY0",viewport=virt3d["viewport"][0], x=50, y=510, width=300, min_val=-20.0, max_val=20.0, initial_val=4.0, height=20)
    virt3d["viewport"][0]["slider"]["eyeZ"] = HorizontalSlider(label="EyeZ0",viewport=virt3d["viewport"][0], x=50, y=480, width=300, min_val=-20.0, max_val=20.0, initial_val=4.0, height=20)

    virt3d["viewport"][0]["slider"]["theta_RA1"] = HorizontalSlider(label="theta_RA1",viewport=virt3d["viewport"][0], x=450, y=110, width=300, min_val=-180.0, max_val=180.0, initial_val=90.0, height=20)
    virt3d["viewport"][0]["slider"]["gamma_RA2"] = HorizontalSlider(label="gamma_RA2",viewport=virt3d["viewport"][0], x=450, y=80, width=300, min_val=-180.0, max_val=180.0, initial_val=90.0, height=20)
    virt3d["viewport"][0]["slider"]["gamma_RA3"] = HorizontalSlider(label="gamma_RA3",viewport=virt3d["viewport"][0], x=450, y=50, width=300, min_val=-180.0, max_val=180.0, initial_val=180.0, height=20)

    virt3d["viewport"][0]["slider"]["offtheta_RA1"] = HorizontalSlider(label="offtheta_RA1",viewport=virt3d["viewport"][0], x=50, y=110, width=300, min_val=-180.0, max_val=180.0, initial_val=90.0, height=20)
    virt3d["viewport"][0]["slider"]["offgamma_RA2"] = HorizontalSlider(label="offgamma_RA2",viewport=virt3d["viewport"][0], x=50, y=80, width=300, min_val=-180.0, max_val=180.0, initial_val=90.0, height=20)
    virt3d["viewport"][0]["slider"]["offgamma_RA3"] = HorizontalSlider(label="offgamma_RA3",viewport=virt3d["viewport"][0], x=50, y=50, width=300, min_val=-180.0, max_val=180.0, initial_val=180.0, height=20)

    pygame.init()
    glutInit()
    pygame.display.set_mode(virt3d["camera"]["display"], DOUBLEBUF | OPENGL)

    # Define points and lines
    virt3d["viewport"][0]["objects"] = {}
    virt3d["viewport"][0]["objects"]["points"] = [
        [0, 0, 0],
        [0, 0, 1],
        [1, 0, 2],
        [2, 0, 2]
    ]

    virt3d["viewport"][0]["objects"]["lines"] = [
        (0, 1),
        (1, 2),
        (2, 3)
    ]

    virt3d["time"] = 0
    return virt3d

def drawAxes(length=2.0):
    glLineWidth(2)
    glBegin(GL_LINES)

    # X-axis (red)
    glColor3f(1, 0, 0)
    glVertex3fv([0, 0, 0])
    glVertex3fv([length, 0, 0])

    # Y-axis (green)
    glColor3f(0, 1, 0)
    glVertex3fv([0, 0, 0])
    glVertex3fv([0, length, 0])

    # Z-axis (blue)
    glColor3f(0, 0, 1)
    glVertex3fv([0, 0, 0])
    glVertex3fv([0, 0, length])

    glEnd()


def drawObjects(objects):

    # Draw points
    glPointSize(8)
    glBegin(GL_POINTS)
    glColor3f(1, 1, 1)
    for p in objects["points"]:
        glVertex3fv(p)
    glEnd()

    # Draw lines
    glBegin(GL_LINES)
    glColor3f(1, 1, 0)
    for l in objects["lines"]:
        glVertex3fv(objects["points"][l[0]])
        glVertex3fv(objects["points"][l[1]])
    glEnd()



def moveVirtual3dObjects(virt3d, bnsensors, bnrobot):
    return

def updateVirtual3dEnvironment(virt3d):
    
    # Check events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

        # Handle key presses
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False

        for viewport in virt3d["viewport"]:
            for slider in viewport["slider"]:
                viewport["slider"][slider].handle_event(event)

    #print(virt3d["camera"])
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


    for viewport in virt3d["viewport"]:

        glViewport( viewport["start"][0], viewport["start"][1], viewport["size"][0], viewport["size"][1])
        setOrthoProjection(virt3d, viewport)
        drawAxes()
        drawObjects(viewport["objects"])
        for slider in viewport["slider"]:
            viewport["slider"][slider].draw()


    pygame.display.flip()

    return True


def setRoboticArmsPoints(virt3d, point0, point1, point2, point3 ):

    virt3d["viewport"][0]["objects"]["points"] = [
        point0,
        point1,
        point2,
        point3,
    ]


def getAngles(virt3d):

    return [
        virt3d["viewport"][0]["slider"]["theta_RA1"].get_value(),
        virt3d["viewport"][0]["slider"]["gamma_RA2"].get_value(),
        virt3d["viewport"][0]["slider"]["gamma_RA3"].get_value(),
    ]

def getOffsets(virt3d):

    return [
        virt3d["viewport"][0]["slider"]["offtheta_RA1"].get_value(),
        virt3d["viewport"][0]["slider"]["offgamma_RA2"].get_value(),
        virt3d["viewport"][0]["slider"]["offgamma_RA3"].get_value(),
    ]
     

def wait(time):
    pygame.time.wait(time)

def quit():
    pygame.quit()

