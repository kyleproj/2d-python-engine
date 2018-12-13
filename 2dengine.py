import sys
import sdl2 as sdl
import sdl2.ext as sdle
import time
import random
from multiprocessing.dummy import Pool as ThreadPool
from ctypes import *
import math
import array
import sys
from PIL import Image
sys.setrecursionlimit(10000)

def getColor(r, g, b, a):
    return (r << 16 | g << 8 | b)

def getPixel(x, y, sx):
    return sx * y + x

class TimeManager:
    currentTime = time.time()
    startTime = currentTime
    previousTime = currentTime
    tickTime = 0.0
    ticks = 0.0
    duration = 0.0
    timers = {}

    def tick(self):
        self.duration = self.currentTime - self.startTime
        self.tickTime = self.currentTime - self.previousTime
        self.previousTime = self.currentTime 
        self.currentTime = time.time()
        self.ticks=self.ticks+1
        if self.ticks > 1000000:
            self.ticks = 0

    def setTimer(self, name, curTime):
        self.timers[name] = curTime 

    def getTimer(self, name):
        return self.timers[name]

class Sprite:
    sx = 0
    sy = 0
    pixels = None
    name = ""

    def __init__(self, name):
        self.name = name

    def loadImage(self, filename):
        img = Image.open(filename)
        pixels = img.load()
        self.sx, self.sy = img.size
        pixelSize = self.sx * self.sy
        self.pixels = [0]*pixelSize
        for x in range(0, self.sx):
            for y in range(0, self.sy):
                r, g, b, a = pixels[x, y]
                self.pixels[getPixel(x, y, self.sx)] = getColor(r, g, b, a)

class Entity:
    sprites = {}
    x = 0
    y = 0
    px = 0
    py = 0
    #sx = 0
    #sy = 0
    xspeed = 0
    yspeed = 0
    currentSprite = ""
    name = ""

    def __init__(self, name, defaultSprite):
        self.currentSprite = defaultSprite 
        self.name = name

    def addSprite(self, sprite):
        self.sprites[sprite.name] = sprite

    def sprite(self):
        return self.sprites[self.currentSprite]

class Renderer:
    WINDOW_X = 1280
    WINDOW_Y = 960
    PIXCNT=WINDOW_X*WINDOW_Y
    scale = 5
    pixels = array.array('i', [c_int(0).value for i in range(PIXCNT)])
    pitch = c_int()
    frameCount = 0
    backgroundColor=sdle.Color(0, 0, 0)
    previousFrameTime = 0
    setPixels = []

    def __init__(self, entities, timer):
        self.entities = entities
        self.timer=timer
        self.window = sdle.Window("Game", size=(self.WINDOW_X, self.WINDOW_Y))
        self.renderer = sdle.Renderer(self.window, flags=sdl.SDL_RENDERER_ACCELERATED)
        self.texture = sdl.SDL_CreateTexture(self.renderer.renderer, sdl.SDL_PIXELFORMAT_ARGB8888, sdl.SDL_TEXTUREACCESS_STREAMING, self.WINDOW_X, self.WINDOW_Y)
        self.window.show()

    def blit(self, _x, _y, _sx, _sy):
        sdl.SDL_UpdateTexture(self.texture, None, c_void_p(self.pixels.buffer_info()[0]), c_int(self.WINDOW_X*4))
        sdl.SDL_RenderCopy(self.renderer.renderer, self.texture, None, None)
        self.renderer.present() 

    def drawRect(self, _x, _y, _sx, _sy, r, g, b, a=255):
        for y in range(_y, _y+_sy, 1):
            if y >= self.WINDOW_Y - 1 or y < 0:
                continue
            for x in range(_x, _x+_sx, 1):
                if x >= self.WINDOW_X-1 or x < 0:
                    continue
                self.pixels[c_int(getPixel(x, y, self.WINDOW_X)).value] = c_int(getColor(r, g, b, a)).value

    def setPixel(self, x, y, color):
        #if x >=0 and y >=0 and x < self.WINDOW_X and y < self.WINDOW_Y:
        self.pixels[c_int(getPixel(x, y, self.WINDOW_X)).value] = color 
        self.setPixels.append([x,y])

    def drawSprite(self, sprite, ex, ey):
        for y in range(sprite.sy):
            #if y >= self.WINDOW_Y - 1 or y < 0 or y >= sprite.sy:
            #    continue
            for x in range(sprite.sx):
                #if x >= self.WINDOW_X-1 or x < 0 or x >= sprite.sx:
                #    continue
                self.setPixel(x+ex, y+ey, sprite.pixels[getPixel(x, y, sprite.sx)])

    def clearScreen(self):
        for x, y in self.setPixels:
            self.pixels[c_int(getPixel(x, y, self.WINDOW_X)).value] = 0
        self.setPixels = []

    def render(self):

        self.clearScreen() 
        for k, e in self.entities.items():
            self.drawSprite(e.sprites[e.currentSprite], e.x, e.y)

        self.blit(0, 0, self.WINDOW_X, self.WINDOW_Y)

        self.frameCount = self.frameCount+1
        if self.timer.currentTime - self.previousFrameTime >= 1.0:
            print ("fps:", self.frameCount)
            self.previousFrameTime = self.timer.currentTime 
            self.frameCount=0


class Game:
    entities = {}
    gameSpeed = 0 
    running = False
    grid=[]
    collisions=[]

    def __init__(self):
        self.running = True
        self.timer = TimeManager()
        self.renderer = Renderer(self.entities, self.timer)
        startTime = time.time()
        self.gameSpeed = 1.0/60.0
        s=Sprite('test')
        s.loadImage('test.png')
        e=Entity('test', 'test')
        e.x=50
        e.y=50
        e.addSprite(s)
        self.addEntity(e)
        self.gridSize=40
        self.gridx = int(self.renderer.WINDOW_X/self.gridSize)
        self.gridy = int(self.renderer.WINDOW_Y/self.gridSize)
        self.grid = [["" for y in range(self.gridy)] for x in range(self.gridx)]
        print (self.gridx, self.gridy, len(self.grid), len(self.grid[0]))
        for i in range(0, 10):
            s=Sprite('ai')
            s.loadImage('test.png')
            e=Entity('ai' + str(i), 'ai')
            e.x=300+random.randint(50, self.renderer.WINDOW_X-50)
            e.y=300+random.randint(50, self.renderer.WINDOW_Y-50)
            if e.x+s.sx >= self.renderer.WINDOW_X:
                e.x = self.renderer.WINDOW_X-(1+s.sx)
            if e.y+s.sy >= self.renderer.WINDOW_Y:
                e.y = self.renderer.WINDOW_Y-(1+s.sy)
            e.xspeed=random.randint(-10, 10)
            e.yspeed=random.randint(-10, 10)
            e.addSprite(s)
            self.addEntity(e)
        self.keys = {}

    def addEntity(self, entity):
        self.entities[entity.name] = entity 

    def updateGame(self):
        for i in range(0, 10):
            e = self.entities['ai' + str(i)]
            e.xspeed+=((i*10+int(math.sin(self.timer.duration*e.xspeed/100.0))*50+int(math.sin(self.timer.duration*e.xspeed/100.0)*60))/100.0 - random.randint(1, 10)/10.0)/2.5
            e.yspeed+=((int(math.cos(self.timer.duration*e.yspeed/100.0))*50+int(math.cos(self.timer.duration*e.yspeed/100.0)*80))/100.0 - random.randint(1, 10)/6.3)/2.5

        for k, e in self.entities.items():
            s = e.sprite()
            e.px=e.x
            e.py=e.y
            e.x+=int(e.xspeed)
            e.y+=int(e.yspeed)
            e.xspeed = e.xspeed/1.02
            e.yspeed = e.yspeed/1.02
            if e.x+s.sx >= self.renderer.WINDOW_X or e.x <= 0:
                e.xspeed=e.xspeed*-1
                e.x = e.px #self.renderer.WINDOW_X-s.sx
                e.x+=int(e.xspeed)
            if e.y+s.sy >= self.renderer.WINDOW_Y or e.y <= 0:
                e.yspeed=e.yspeed*-1 
                e.y = e.py #self.renderer.WINDOW_Y-s.sy
                e.y+=int(e.yspeed)

            gx = int(e.x/self.gridSize)
            gy = int(e.y/self.gridSize)
            if self.grid[gx][gy] != "" and self.grid[gx][gy] != k:
                self.collisions.append([self.grid[gx][gy], k])
                self.grid[gx][gy] = ""
            else:
                self.grid[gx][gy] = k

        for c in self.collisions:
            l = self.entities[c[0]]
            ls = l.sprite() 
            r = self.entities[c[1]]
            rs = r.sprite() 

            if (l.x+ls.sx > r.x and l.x < r.x+rs.sx and l.y+ls.sy > r.y and l.y < r.y + rs.sy):
                l.x=l.px
                r.x=r.px
                l.xspeed=l.xspeed*-1
                r.xspeed=r.xspeed*-1
                l.x+=int(l.xspeed)
                r.x+=int(r.xspeed)
                l.px=l.x
                r.px=r.x

            if (l.x+ls.sx > r.x and l.x < r.x+rs.sx and l.y+ls.sy > r.y and l.y < r.y + rs.sy):
                l.y=l.py
                r.y=r.py
                l.yspeed=l.yspeed*-1
                r.yspeed=r.yspeed*-1
                l.y+=int(l.yspeed)
                r.y+=int(r.yspeed)
                l.py=l.y
                r.py=r.y

        self.collisions=[]


            
    def keyDown(self, key):
        try:
            return self.keys[key]
        except:
            self.keys[key] = False
        return False

    def checkEvents(self):
        for event in sdle.get_events():
            if event.type == sdl.SDL_QUIT:
                self.running = False
                break
            if event.type == sdl.SDL_KEYDOWN:
                self.keys[event.key.keysym.sym] = True

            if event.type == sdl.SDL_KEYUP:
                self.keys[event.key.keysym.sym] = False

        if self.keyDown(sdl.SDLK_DOWN):
            s = self.entities['test'].sprite()
            self.entities['test'].yspeed = self.entities['test'].yspeed+0.5

        if self.keyDown(sdl.SDLK_UP):
            s = self.entities['test'].sprite()
            self.entities['test'].yspeed = self.entities['test'].yspeed-0.5

        if self.keyDown(sdl.SDLK_RIGHT):
            s = self.entities['test'].sprite()
            self.entities['test'].xspeed = self.entities['test'].xspeed+0.5

        if self.keyDown(sdl.SDLK_LEFT):
            s = self.entities['test'].sprite()
            self.entities['test'].xspeed = self.entities['test'].xspeed-0.5
   
    def run(self):
        while self.running:
            self.timer.tick()
            self.checkEvents()
            self.updateGame()
            self.renderer.render()
            delta = (time.time() - self.timer.currentTime)
            sleepTime = self.gameSpeed - delta
            if sleepTime > 0:
                sdl.SDL_Delay(int(sleepTime*1000))

        return 0

    def __del__(self):
        return 0

if __name__ == "__main__":
    sdle.init()
    g = Game() 
    sys.exit(g.run())
    sdle.quit()
