import sys
from tokenizer import Tokenizer

class Parser:
    def __init__(self, filename):
        self.tokenizer = Tokenizer(filename = filename)
        # current input TOKEN
        self.inputSym = self.tokenizer.getNext()

    # advance to next token
    def next(self):
        self.inputSym = self.tokenizer.getNext()

    def checkFor(self, token):
        if self.inputSym == token:
            self.next()
        else:
            raise Exception
    
    def parse(self):
        self.computation()
        print("")

    # "main" {varDecl} {funcDecl} "{" statSequence "}" "."
    def computation(self):
        self.checkFor(200)
        # varDecl = typeDecl...  = "var"|"array"...
        while self.inputSym == 110 or self.inputSym == 111:
            self.varDecl()
        # funcDecl = ["void"] "function"
        while self.inputSym == 112 or self.inputSym == 113:
            self.funcDecl()
        # "{"
        self.checkFor(150)
        self.statSequence()
        # "}"
        self.checkFor(80)
        # "."
        self.checkFor(30)
    
    # { varDecl } "{" [ statSequence ] "}"
    def funcBody(self):
        # funcBody = varDecl... = typeDecl... = "var"|"array" <- tokens to look ahead
        while self.inputSym == 110 or self.inputSym == 111:
            self.varDecl()
        # "{"
        self.checkFor(150)
        # statSequence = statement... = statement...
        # = assignment = "let"...
        # = funcCall = "call"...
        # = ifStatement = "if"...
        # = whileStatement = "while"...
        # = returnStatement = "return"...
        if self.inputSym in [100, 101, 102, 103, 104]:
            self.statSequence()
        # "}"
        self.checkFor(80)

    # "(" [ident { "," ident }] ")"
    # TODO array of params
    def formalParam(self):
        # "("
        self.checkFor(50)
        # ident
        if self.inputSym == 61:
            self.checkFor(61)
            # ","
            while self.inputSym == 30:
                self.checkFor(30)
                # ident
                self.checkFor(61)
        # ")"
        self.checkFor(35)

    def funcDecl(self):
        # ["void"]
        if self.inputSym == 112:
            self.checkFor(112)
        # "function"
        self.checkFor(113)
        # ident
        self.checkFor(61)
        self.formalParam()
        # ";"
        self.checkFor(70)
        self.funcBody()
        # ";"
        self.checkFor(70)

    # typeDecl indent { "," ident } ";"
    def varDecl(self):
        self.typeDecl()
        self.checkFor(61)
        while self.inputSym == 31:
            self.checkFor(31)
            self.checkFor(61)
        self.checkFor(70)

    # "var" |   "array" "[" number "]" { "[" number "]" }
    def typeDecl(self):
        # "var"
        if self.inputSym == 110:
            self.checkFor(110)
        elif self.inputSym == 111:
            self.checkFor(111)
                # "["
            self.checkFor(32)
            # number
            self.checkFor(60)
            # "]"
            self.checkFor(34)
            while self.inputSym == 32:
                self.checkFor(32)
                self.checkFor(60)
                self.checkFor(34)
        else:
            raise Exception

    # statement { ";" statement } [";"]
    def statSequence(self):
        self.statement()
        # ";"
        while self.inputSym == 70:
            self.checkFor(70)
            # statement
            if self.inputSym in [100, 101, 102, 103, 104]:
                self.statement()
            # teminating semicolon optional
            else:
                break

    # statement      lookaheads
    # = assignment = "let"...
    # = funcCall = "call"...
    # = ifStatement = "if"...
    # = whileStatement = "while"...
    # = returnStatement = "return"...
    def statement(self):
        # "let" 
        if self.inputSym == 100:
            self.assignment()
        # "call"
        elif self.inputSym == 101:
            self.funcCall()
        # "if"
        elif self.inputSym == 102:
            self.ifStatement()
        # "while"
        elif self.inputSym == 103:
            self.whileStatement()
        # "return"
        elif self.inputSym == 104:
            self.returnStatement()

    # "let" designator "<-" expression
    def assignment(self):
        self.checkFor(100)
        self.designator()
        self.checkFor(40)
        self.expression()
    
    # "call" ident [ "(" [expression { "," expression } ] ")" ]
    def funcCall(self):
        self.checkFor(101)
        self.checkFor(61)
        # function with parentheses
        if self.inputSym == 50:
            self.checkFor(50)
            # expression is optional
            # expression = ... = factor... 
            # = designator = indent
            # = number
            # = "("...
            # = funcCall = "call"...
            if self.inputSym in [60, 61, 50, 101]:
                self.expression()
                # ","
                while self.inputSym == 30:
                    self.checkFor(30)
                    self.expression()
                # matching closing parenthese
            self.checkFor(35)
        # function without parentheses, no parameters allowed
    
    # "if" relation "then" statSequence [ "else" statSequence ] "fi"
    def ifStatement(self):
        self.checkFor(102)
        self.relation()
        self.checkFor(41)
        self.statSequence()
        # optional "else" sequence
        if self.inputSym == 90:
            self.checkFor(90)
            self.statSequence()
        self.checkFor(82)

    # "while" relateion "do" statSequence "od"
    def whileStatement(self):
        self.checkFor(103)
        self.relation()
        self.checkFor(42)
        self.statSequence()
        self.checkFor(81)
    
    # "return" [ expression ]
    def returnStatement(self):
        self.checkFor(104)
        # expression = term... = factor... 
        # = designator = indent
        # = number
        # = "("...
        # = funcCall = "call"...
        if self.inputSym in [60, 61, 50, 101]:
            self.expression()

    # ident { "[" expression "]" }
    def designator(self):
        self.checkFor(61)
        while self.inputSym == 32:
            self.checkFor(32)
            self.expression()
            self.checkFor(34)

    # designator|number|"(" expression ")"|funcCall
    # = designator = indent
    # = number
    # = "("...
    # = funcCall = "call"...
    def factor(self):
        if self.inputSym == 61:
            self.designator()
        elif self.inputSym == 60:
            # TODO
            self.checkFor(60)
        elif self.inputSym == 50:
            self.checkFor(50)
            self.expression()
            self.checkFor(35)
        elif self.inputSym == 101:
            self.funcCall()
        else:
            raise Exception
    
    # factor { ("*"|"/") factor}
    def term(self):
        self.factor()
        while self.inputSym == 1 or self.inputSym == 2:
            if self.inputSym == 1:
                self.checkFor(1)
            else:
                self.checkFor(2)
            self.factor()
    
    def expression(self):
        self.term()
        while self.inputSym == 11 or self.inputSym == 12:
            if self.inputSym == 11:
                self.checkFor(11)
            else:
                self.checkFor(12)
            self.term()

    # expression relOp expression
    def relation(self):
        self.expression()
        if self.inputSym in [20, 21, 22, 23, 24,25]:
            self.checkFor(self.inputSym)
        else:
            raise Exception
        self.expression()

def main():
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        # raise Exception
    else:
        filename = "sample2"
    # pass filename as argument
    parser = Parser(filename)
    # parser = Parser("source_code_input")
    parser.parse()

if __name__ == "__main__":
    main()