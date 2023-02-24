digit = set([chr(i+48) for i in range(10)])
# lower case only
letter = set([chr(i+97) for i in range(26)] + [chr(i+65) for i in range(26)])
token_table = { 
    # "error": 0,
    "*":1,
    "/":2,
    "+":11,
    "-":12,
    "==":20,
    "!=":21,
    "<":22,
    ">=":23,
    "<=":24,
    ">":25,
    ".":30,
    ",":31,
    "[":32,
    "]":33,
    ")":35,
    "<-":40,
    "then":41,
    "do":42,
    "(":50,
    # "number" and "identifier" can be var names
    # "number":60,
    # "identifier":61,
    ";":70,
    "}":80,
    "od":81,
    "fi":82,
    "else":90,
    "let": 100,
    "call": 101,
    "if": 102,
    "while": 103,
    "return": 104,
    "var": 110,
    "array": 111,
    "void": 112,
    "function": 113,
    "procedure": 114,
    "{": 150,
    "main": 200
    # "eof": 255
}

# new id of identifier = len(ident) + 1
ident = {
    "InputNum":0,
    "OutputNum":1,
    "OutputNewLine":2
}

class FileReader():
    def __init__(self, filename):
        self.filename = filename
        self.file = None
        self.FileReader()

    def getNext(self):
        char = self.file.read(1)
        # end of file
        # if char == "":
            # exit()
        # ignore space, but need space to separate two key words etc.
        # if char == " ":
            # return self.getNext()
        # ignore space in tokenizer
        return char

    def Error(self):
        raise Exception
    
    def FileReader(self):
        # read text mode
        self.file = open(self.filename, "rt")

class Tokenizer():
    def __init__(self, filename = ""): 
        self.filereader = FileReader(filename)
        self.inputSym = None
        self.number = None
        self.id = None
        self.next()
    
    # get next input char
    def next(self):
        self.inputSym = self.filereader.getNext()

    # get next input token
    def getNext(self):
        token = -1
        if self.inputSym in digit:
            self.number = 0
            token = 60
            while self.inputSym in digit:
                self.number *= 10
                self.number += ord(self.inputSym) - 48
                self.next()
        elif self.inputSym in letter:
            word = ""
            while self.inputSym in letter or self.inputSym in digit:
                word += self.inputSym
                self.next()
            # keyword
            if word in token_table:
                token = token_table[word]
            # variable or function?
            # TODO
            else:
                token = 61
                self.id = word
        elif self.inputSym in ["+","-","*","/","(",")",",","[","]",")","(",";","}","{"]:
            token = token_table[self.inputSym]
            self.next()
        elif self.inputSym == ".":
            token = token_table["."]
            self.next()
            # call next and get eof token 255
        elif self.inputSym in ["=","!","<",">"]:
            if self.inputSym == "=":
                self.next()
                if self.inputSym == "=":
                    token = token_table["=="]
                    self.next()
                else:
                    raise Exception
            elif self.inputSym == "!":
                self.next()
                if self.inputSym == "=":
                    token = token_table["!="]
                    self.next()
                else:
                    raise Exception
            elif self.inputSym == "<":
                self.next()
                if self.inputSym == "=":
                    token = token_table["<="]
                    self.next()
                elif self.inputSym == "-":
                    token = token_table["<-"]
                    self.next()
                else:
                    token = token_table["<"]
            elif self.inputSym == ">":
                self.next()
                if self.inputSym == "=":
                    token = token_table[">="]
                    self.next()
                else:
                    token = token_table[">"]
        # handling eof
        elif self.inputSym == "":
            return 255
        # handling space tab and line change
        else:
            if self.inputSym == "\n":
                print()
            # advance to next char
            self.next()
            # try to return next token
            return self.getNext()
        print(token,end=" ")
        return token
    
    # can't think about elegant variable table solution
    def Id2String(self, id):
        for k, v in ident:
            if v == id:
                return k
        return None

    def String2Id(self, name):
        if name not in ident:
            ident[name] = len(ident)
        return ident[name] 