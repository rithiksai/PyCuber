from .algorithm import *
from .util import FrozenDict
from functools import reduce
from itertools import permutations

class Square(object):
    """Square(colour), implements a square (sticker) on a cube."""
    def __init__(self, colour, parent=None, children=[]):
        super(Square, self).__init__()
        if isinstance(colour, Square):
            colour = colour.colour
        if not isinstance(colour, str):
            raise TypeError("Square.__init__() argument must be Square or str, got {0}."
                    .format(colour.__class__.__name__))
        if colour not in ["red", "yellow", "green", "white", "orange", "blue", "unknown"]:
            raise ValueError("Square colour must be "
                    "red, yellow, green, white, orange, blue or unknown, "
                    "not {0}.".format(colour))
        self.colour = colour
        self.parent = parent
        self.children = set(children)

    def __repr__(self):
        """
        Print out two spaces with background colour.
        """
        return {
            "red":"\x1b[45m", 
            "yellow":"\x1b[43m", 
            "green":"\x1b[42m", 
            "white":"\x1b[47m", 
            "orange":"\x1b[41m", 
            "blue":"\x1b[46m", 
            "unknown":"\x1b[40m", 
            }[self.colour] + "  \x1b[49m"

    def  __eq__(self, another):
        """
        Check if the colour is as same as another.
        """
        if isinstance(another, Square):
            return self.colour == another.colour
        return False
    
    def __ne__(self, another):
        """
        Check if the colours are different.
        """
        return not self.__eq__(another)
    
    def __hash__(self):
        """
        Square object is hashable.
        """
        colour_to_hex = {
            "red":0xFF0000, 
            "yellow":0xFFFF00, 
            "green":0x00FF00, 
            "white":0xFFFFFF, 
            "orange":0xFFA500, 
            "blue":0x0000FF, 
            }
        return hash(str(self)) + colour_to_hex[self.colour]

    def copy(self):
        """
        Copy this Square.
        """
        return Square(self.colour)


class Cuboid(object):
    """
    Cuboid(**kwargs), implements a cuboid on the Cube.
    ex: Cuboid(U=Square("yellow"), F=Square("green"), L=Square("red"))
    """
    def __init__(self, parent=None, children=[], **kwargs):
        super(Cuboid, self).__init__()
        for kw in kwargs:
            if kw not in list("LUFDRB"):
                raise ValueError(
                    "Facings must be L U F D R B, not {0}."
                    .format(kw), 
                    )
            elif isinstance(kwargs[kw], str):
                kwargs[kw] = Square(kwargs[kw])
        self.facings = FrozenDict(kwargs)
        self.parent = parent
        self.children = set(children)
        self.location = "".join(kwargs)

    def __repr__(self):
        """
        Print out "Cuboid(U:\x1b[43m ...)"
        """
        return "{0}({1})".format(
            self.__class__.__name__, 
            str(self.facings)[1:-1], 
            )

    def __getitem__(self, face):
        """
        Cuboid["L"] => Returns the square that positioned at L face.
        """
        return self.facings[face]

    def __hash__(self):
        """
        Cuboid object is hashable.
        """
        return reduce(
            lambda x, y: hash(x) + hash(y), 
            self.facings.values(), 
            list(self.facings.values())[0], 
            ) // hash(self.__class__.__name__)

    def __eq__(self, another):
        """
        Check if two Cuboids are the same.
        """
        if isinstance(another, Cuboid):
            return self.facings == another.facings
        return False

    def __ne__(self, another):
        """
        Check if two Cuboids are different.
        """
        return not self.__eq__(another)

    def __contains__(self, value):
        """
        Check if the Cuboid uses that face.
        """
        return value in self.facings

    def __or__(self, value):
        """
        Check if the Cuboid uses that colour.
        """
        try:
            return Square(value) in self.facings.values()
        except ValueError:
            return False

    def __and__(self, another):
        """
        Check if two Cuboids have the same location.
        """
        if isinstance(another, str):
            return tuple(self.facings) in permutations(another, len(another))
        try:
            return self.facings.viewkeys() == another.facings.viewkeys()
        except AttributeError:
            return self.facings.keys() == another.facings.keys()

    def copy(self):
        """
        Copy this Cuboid.
        """
        try:
            new = {
                "centre": Centre, 
                "edge": Edge, 
                "corner": Corner, 
                }[self.type](
                    parent=self.parent, 
                    children=self.children, 
                    **self.facings
                    )
        except AttributeError:
            new = Cuboid(
                parent=self.parent, 
                children=self.children, 
                **self.facings
                )
        return new


class Centre(Cuboid):
    """
    Centre(U=Square("yellow")) => Implements the "Centre Block" (has 1 sticker).
    """
    def __init__(self, parent=None, children=[], **kwargs):
        if len(kwargs) != 1:
            raise ValueError("A Centre has 1 Square, got {0}.".format(len(kwargs)))
        super(Centre, self).__init__(parent, children, **kwargs)
        self.type = "centre"
        self.face = list(kwargs.keys())[0]

    @property
    def colour(self):
        return list(self.facings.values())[0].colour

 
class Edge(Cuboid):
    """
    Edge(U=Square("yellow"), F=Square("green")) => Implements the "Edge Block" (has 2 stickers).
    """
    def __init__(self, parent=None, children=[], **kwargs):
        if len(kwargs) != 2:
            raise ValueError("An Edge has 2 Squares, got {0}.".format(len(kwargs)))
        super(Edge, self).__init__(parent, children, **kwargs)
        self.type = "edge"


class Corner(Cuboid):
    """
    Corner(
        U=Square("yellow"), 
        F=Square("green"), 
        R=Square("orange"), 
        ) => Implements the "Corner Block" (has 3 stickers).
    """
    def __init__(self, parent=None, children=[], **kwargs):
        if len(kwargs) != 3:
            raise ValueError("A Corner has 3 Squares, got {0}.".format(len(kwargs)))
        super(Corner, self).__init__(parent, children, **kwargs)
        self.type = "corner"


class Cube(object):
    """
    Cube([, {a set of Cuboids}]) => Implements a Rubik's Cube.
    """
    def __init__(self, cuboids=None):
        super(Cube, self).__init__()
        self.parent = None
        self.children = set()
        if not cuboids:
            cuboids = set()
            colours = {"L":"red", "U":"yellow", "F":"green", "D":"white", "R":"orange", "B":"blue"}
            for loc in [
                "LDB", "LDF", "LUB", "LUF", "RDB", "RDF", "RUB", "RUF", 
                "LB", "LF", "LU", "LD", "DB", "DF", "UB", "UF", "RB", "RF", "RU", "RD", 
                "L", "R", "U", "D", "F", "B", 
                ]:
                if len(loc) == 3:
                    cuboids.add(Corner(**{loc[i]:Square(colours[loc[i]]) for i in range(3)}))
                elif len(loc) == 2:
                    cuboids.add(Edge(**{loc[i]:Square(colours[loc[i]]) for i in range(2)}))
                else:
                    cuboids.add(Centre(**{loc[0]:Square(colours[loc[0]])}))
        if isinstance(cuboids, set):
            for cubie in cuboids:
                if isinstance(cubie, Cuboid):
                    children = set()
                    for sqr in cubie.facings.values():
                        children.add(Square(sqr))
                    if len(cubie.location) == 3:
                        child_class = Corner
                    elif len(cubie.location) == 2:
                        child_class = Edge
                    elif len(cubie.location) == 1:
                        child_class = Centre
                    self.children.add(child_class(parent=self, children=children, **cubie.facings))
                else:
                    raise ValueError("Should use Cuboid, not {0}.".format(cubie.__class__.__name__))

    def __repr__(self):
        """
        Draw the Cube as expanded view.
        """
        result = ""
        _ = {
            "L": self.L, 
            "U": self.U, 
            "F": self.F, 
            "D": self.D, 
            "R": self.R, 
            "B": self.B, 
            }
        for i in range(3):
            result += "      " + "".join(str(square) for square in _["U"][i]) + "\n"
        for i in range(3):
            for side in "LFRB":
                result += "".join(str(square) for square in _[side][i])
            result += "\n"
        for i in range(3):
            result += "      " + "".join(str(square) for square in _["D"][i]) + "\n"
        return result


    def __getitem__(self, key):
        """
        Get specific Cuboid by location.
        """
        for child in self.children:
            if child & key:
                return child
        raise KeyError(str(key))

    def __setitem__(self, key, value):
        """
        Reset a specific Cuboid.
        """
        if self[key].type != value.type:
            raise ValueError(
                "Replacement of {0} must be {1}, not {2}."
                .format(key, self[key].type, value.type), 
                )
        if not self[key] & value:
            raise ValueError(
                "Location must be {0}, not {1}."
                .format(key, value.location), 
                )
        q = self[key]
        self.children.remove(q)
        q.facings = value.facings
        q.children = set(value.facings.values())
        self.children.add(q)

    def __getattr__(self, name):
        """
        Returns the face from Cube.get_face() if the name is L U F D R or B.
        """
        if name in list("LUFDRB"):
            return self.get_face(name)
        else:
            return super(Cube, self).__getattribute__(name)

    def __call__(self, algo):
        """
        A shortcut for Cube.perform_algo().
        """
        return self.perform_algo(algo)
    
    def __iter__(self):
        """
        Iterate over every Cuboid in the Cube.
        """
        result = []
        for loc in [
            "BDL", "FDL", "ULF", "ULB", "RUF", "RUB", "RDB", "RDF", 
            "LU", "FU", "RU", "BU", "LF", "LB", "RF", "RB", "FD", "LD", "BD", "RD", 
            "F", "U", "R", "L", "D", "B"
            ]:
            result.append((loc, self[loc]))
        return iter(result)

    def __eq__(self, another):
        """
        Check if two Cubes are the same.
        """
        return dict(self) == dict(another)

    def __ne__(self, another):
        """
        Check if two Cubes aren't the same.
        """
        return not self.__eq__(another)

    def at_face(self, face):
        """
        Find all Cuboids which have a Square on specific face.
        """
        return set(
            child for child in self.children
            if face in child.location
            )

    def has_colour(self, colour):
        """
        Find all Cuboids which has a specific colour(s).
        """
        return set(
            child for child in self.children
            if colour in map(
                lambda x: x.colour, 
                child.children, 
                )
            )

    def select_type(self, tp):
        """
        Find all Cuboids which has the specific type.
        """
        return set(
            child for child in self.children
            if tp == child.type
            )

    def get_face(self, face):
        """
        Getting specific face on a Cube.
        Returns as a 2D list.
        """
        if face not in [
            "L", "U", "F", "D", "R", "B", 
            "left", "up", "front", "down", "right", "back"
            ]:
            raise ValueError("Face must be L U F D R B, not {0}.".format(face))
        elif face.islower():
            face = face[0].upper()
        result = [[None] * 3, [None] * 3, [None] * 3]
        ordering = {
            "L": "UDBF", 
            "R": "UDFB", 
            "U": "BFLR", 
            "D": "FBLR", 
            "F": "UDLR", 
            "B": "UDRL", 
            }[face]
        for cuboid in self.at_face(face):
            loc = [None, None]
            for f in cuboid.facings:
                if cuboid.type == "centre":
                    loc = [1, 1]
                if f != face:
                    if cuboid.type == "edge":
                        loc[ordering.index(f) // 2] = (ordering.index(f) % 2) * 2
                        loc[loc.index(None)] = 1
                    elif cuboid.type == "corner":
                        loc[ordering.index(f) // 2] = (ordering.index(f) % 2) * 2
            result[loc[0]][loc[1]] = cuboid.facings[face]
        return result

    def _single_layer(self, step):
        """
        Helper function for Cube.perform_step().
        Perform single layer steps.
        """
        step = Step(step)
        movement = {
            "U": "RFLB", 
            "D": "LFRB", 
            "R": "FUBD", 
            "L": "FDBU", 
            "F": "URDL", 
            "B": "ULDR", 
            "M": ("LR", "FDBU"), 
            "S": ("FB", "URDL"), 
            "E": ("UD", "LFRB"), 
            }[step.face]
        if len(movement) == 2: slice_, movement = movement
        if step.is_inverse: movement = movement[::-1]
        if step.face not in "MSE":
            to_move = {c.copy() for c in self.at_face(step.face)}
        else:
            to_move = {
                c.copy()
                for c in (self.children - self.at_face(slice_[0]) - self.at_face(slice_[1]))
                }
        for cuboid in to_move:
            new = {}
            for f in cuboid.facings:
                if f != step.face:
                    new[movement[(movement.index(f) + step.is_180 + 1) % 4]] = cuboid.facings[f]
                else:
                    new[f] = cuboid.facings[f]
            new_cuboid = {
                "centre": Centre, 
                "edge": Edge, 
                "corner": Corner, 
                }[cuboid.type](
                    parent=self, 
                    children=new.values(), 
                    **new 
                    )
            self[new_cuboid.location] = new_cuboid
        return self

    def _other_rotations(self, step):
        """
        Helper function for Cube.perform_step().
        Perform wide rotations or cube rotations.
        """
        step = Step(step)
        movement = {
            "x": ["L'", "M'", "R"], 
            "y": ["U", "E'", "D'"], 
            "z": ["F", "S", "B'"], 
            "r": ["R", "M'"], 
            "l": ["L", "M"], 
            "u": ["U", "E'"], 
            "d": ["D", "E"], 
            "f": ["F", "S"], 
            "b": ["B", "S'"], 
            }[step.face]
        for s in movement:
            step_ = Step(s)
            if step.is_inverse: step_ = step_.inverse()
            elif step.is_180: step_ = step_ * 2
            self._single_layer(step_)
        return self

    def perform_step(self, step):
        """
        Perform a Rubik's Cube step.
        Using "Singmaster Notation"
        L R U D F B
        l r u d f b
        M S E
        x y z
        """
        step = Step(step)
        if step.face in "LUFDRBMES":
            return self._single_layer(step)
        else:
            return self._other_rotations(step)

    def perform_algo(self, algo):
        """
        Perform a Rubik's Cube Algorithm.
        Using "Singmaster notation".
        """
        algo = Algo(algo)
        for step in algo:
            self.perform_step(step)
        return self

    def copy(self):
        """
        Copy this Cube.
        """
        return Cube({c[1].copy() for c in self})


