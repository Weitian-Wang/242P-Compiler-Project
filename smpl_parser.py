import sys
from typing import *
from tokenizer import Tokenizer

# map token to ir operator
token_operator_map = {
    60 : "const",
    11 :"add",
    12 :"sub",
    1 :"mul",
    2 :"div",
    # if
    102 :"cmp",
    # while
    103 :"cmp",
    #  :"adda",
    #  :"load",
    #  :"store",
    #  :"phi",
    # .
    30 :"end",
    #  :"bra",
    21 :"bne",
    20 :"beq",
    24 :"ble",
    22 :"blt",
    23 :"bge",
    25 :"bgt"
} 

class Instruction:
    def __init__(self, instruction_id: int, op_code: str, operant1:int = None, operant2:int = None):
        self.instruction_id = instruction_id
        self.op_code: str = op_code
        self.operant1: int = operant1
        self.operant2: int = operant2

    def toString(self) -> str:
        if self.op_code == "const":
            return f'{self.instruction_id}: {self.op_code}' + f' #{self.operant1}'
        return f'{self.instruction_id}: {self.op_code}' + (f' ({self.operant1})' if self.operant1 is not None else '') + (f' ({self.operant2})' if self.operant2 is not None else '')
    
class Basic_Block:
    def __init__(self, bb_id):
        self.bb_id: int = bb_id
        # at most two children
        self.branch: Basic_Block = None
        self.fall_through: Basic_Block = None
        # variable name: value instruction number
        self.ssa_table: Dict[str, int] = {}
        self.instruction_list: List[Instruction] = []
        # dominator of current block = self and dominator of dominators
        self.dominator: set[Basic_Block] = set()
        self.dominator.add(self)

    def instructionToGraph(self):
        instruction_str = '|'.join([instruction.toString() for instruction in self.instruction_list])
        rst = f'bb{self.bb_id}[shape=record, label="<b>BB{self.bb_id}|{{{instruction_str}}}"];'
        return rst
    
    def branchToGraph(self):
        if not self.branch:
            return ""
        rst = f'bb{self.bb_id}:s -> bb{self.branch.bb_id}:n [label="branch"];'
        return rst
    
    def fallThroughToGraph(self):
        if not self.fall_through:
            return ""
        rst = f'bb{self.bb_id}:s -> bb{self.fall_through.bb_id}:n [label="fall-through"];'
        return rst
    
    def dominatorToGraph(self):
        rst = ""
        if not self.dominator:
            return rst
        for dominator in self.dominator:
            if dominator != self:
                rst += f'bb{dominator.bb_id}:b -> bb{self.bb_id}:b [color=blue, style=dotted, lable="dom"];' + "\n"
        return rst

class IR:
    def __init__(self):
        self.bb_list: List[Basic_Block] = []
        self.bb_count: int = 0
        # instruction count
        self.pc: int = 0
        # bb0
        self.bb_list.append(Basic_Block(bb_id=0))
        # bb1
        self.addBB(fall_through=True)
    
    def addBB(self, fall_through: bool = False, branch: bool = False, parent: Basic_Block = None):
        if not parent:
            parent = self.bb_list[self.bb_count]
        self.bb_count += 1
        newBB = Basic_Block(self.bb_count)
        # newBB.ssa_table = parent.ssa_table is shallow copy
        newBB.ssa_table = parent.ssa_table.copy()

        self.bb_list.append(newBB)
        if fall_through:
            parent.fall_through = newBB
        if branch:
            parent.branch = newBB
        return newBB

    def toGraph(self):
        file = open('graph_description', 'w+')
        file.write('digraph G{\n')
        for bb in self.bb_list:
            file.write(bb.instructionToGraph()+'\n')
        for bb in self.bb_list:
            if bb.branch:
                file.write(bb.branchToGraph()+'\n')
            if bb.fall_through:
                file.write(bb.fallThroughToGraph()+'\n')
            # if bb.dominator:
                # file.write(bb.dominatorToGraph())
        file.write('}')
    
    def printSSA(self):
        for bb in self.bb_list:
            print(bb.bb_id, {k: v for k,v in bb.ssa_table.items() if type(v) == int})

    # return const instruction id if constant exits
    # else create new constant then return instruction id
    def immediate(self, value:int) -> int:
        for instruction in self.bb_list[0].instruction_list:
            if instruction.op_code == "const" and instruction.operant1 == value:
                return instruction.instruction_id
        self.bb_list[0].instruction_list.append(Instruction(self.pc, "const", operant1=value))
        self.pc += 1
        return self.immediate(value)

    # find the identifier int the same bb
    # return instruction id
    def getIdent(self, id: str, target: Basic_Block = None) -> int:
        if not target:
            target = self.bb_list[self.bb_count]
        # call existing identifier
        if target.ssa_table.get(id) is not None:
            return target.ssa_table[id]
        else:
            # if try to use uninitialized variable, assign a value of zero
            self.setIdent(id, self.immediate(0), target=target)
            return self.getIdent(id, target=target)

    # declear new identifier or update identifier
    def setIdent(self, id:str, instruction_id:int = None, target: Basic_Block = None) -> None:
        if not target:
            target = self.bb_list[self.bb_count]
        # update identifier or set new identifier
        target.ssa_table[id] = instruction_id

    # add instruction to current bb
    def addInstruction(self, op_code: str, operant1 = None, operant2 = None, target: Basic_Block = None):
        if target is None:
            target = self.bb_list[self.bb_count]
        # Common Subexpression Elimination
        # Exclude phi
        if op_code != "phi":
            for dominator in target.dominator:
                for instruction in dominator.instruction_list:
                    if instruction.op_code == op_code and instruction.operant1 == operant1 and instruction.operant2 == operant2:
                        return instruction
        instruction = Instruction(self.pc, op_code, operant1, operant2)
        target.instruction_list.append(instruction)
        self.pc += 1
        return instruction
    
    def addPhi(self, join_bb: Basic_Block, left_bb: Basic_Block, right_bb: Basic_Block):
        for ident, inst_id in join_bb.ssa_table.items():
            # if not initialized set to constant 0
            if ident not in left_bb.ssa_table or left_bb.ssa_table[ident] is None:
                self.getIdent(id=ident, target=left_bb)
            if ident not in right_bb.ssa_table or right_bb.ssa_table[ident] is None:
                self.getIdent(id=ident, target=right_bb)
            left_inst_id = left_bb.ssa_table.get(ident, None)
            right_inst_id = right_bb.ssa_table.get(ident, None)
            if left_inst_id != right_inst_id:
                join_bb.ssa_table[ident] = self.addInstruction(op_code='phi', operant1=left_inst_id, operant2=right_inst_id, target=join_bb).instruction_id

    def reserveWhilePhi(self, loop_header_bb: Basic_Block, ssa_table_ahead):
        for ident, inst_id in loop_header_bb.ssa_table.items():
            # if not initialized set to constant 0
            left_inst_id = loop_header_bb.ssa_table.get(ident, None)
            right_inst_id = ssa_table_ahead.get(ident, None)
            if left_inst_id != right_inst_id:
                # set operant2 to identifier to search later
                loop_header_bb.ssa_table[ident] = self.addInstruction(op_code='phi', operant1=left_inst_id, operant2=ident, target=loop_header_bb).instruction_id

    def updateWhilePhi(self, loop_header_bb: Basic_Block, loop_body_bb: Basic_Block):
         for phi in loop_header_bb.instruction_list:
            if phi.op_code != 'phi':
                break
            ident = phi.operant2
            phi.operant2 = loop_body_bb.ssa_table[ident]

    def addDominator(self, target_bb: Basic_Block, dominator_bb: Basic_Block):
        for bb in dominator_bb.dominator:
            target_bb.dominator.add(bb)


class Parser:
    def __init__(self, filename):
        self.tokenizer = Tokenizer(filename = filename)
        # current input TOKEN
        self.inputSym = self.tokenizer.getNext()
        self.ir: IR = IR()

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
        self.ir.addInstruction("end")
    
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
            while self.inputSym == 31:
                self.checkFor(31)
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
        type, dimension_list = self.typeDecl()
        self.checkFor(61)
        if type == "var":
            self.ir.setIdent(id=self.tokenizer.id, instruction_id=0)
        if type == "array":
            # add array base address to bb0 as const
            base_addr = self.ir.immediate(value = f'{self.tokenizer.id}_addr')
            self.ir.setIdent(id=self.tokenizer.id, instruction_id = [base_addr, dimension_list])
        while self.inputSym == 31:
            self.checkFor(31)
            self.checkFor(61)
            if type == "var":
                self.ir.setIdent(id=self.tokenizer.id, instruction_id=0)
            if type == "array":
                # add array base address to bb0 as const
                base_addr = self.ir.immediate(value = f'{self.tokenizer.id}_addr')
                self.ir.setIdent(id=self.tokenizer.id, instruction_id = [base_addr, dimension_list])
        self.checkFor(70)

    # "var" |   "array" "[" number "]" { "[" number "]" }
    def typeDecl(self):
        # "var"
        if self.inputSym == 110:
            self.checkFor(110)
            return "var", None
        elif self.inputSym == 111:
            self.checkFor(111)
            # "["
            self.checkFor(32)
            # number assume no out of boundary
            dimension_list = []
            dimension_list.append(self.tokenizer.number)
            self.checkFor(60)
            # "]"
            self.checkFor(34)
            while self.inputSym == 32:
                self.checkFor(32)
                dimension_list.append(self.tokenizer.number)
                self.checkFor(60)
                self.checkFor(34)
            return "array", dimension_list
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
            # snapshot current status
            position = self.tokenizer.snapshot()
            pc = self.ir.pc
            bb = self.ir.bb_count
            ssa_table_ahead = self.whileStatement(preRun=True)
            # recover status
            self.tokenizer.rewind(position)
            # clear const instructions in bb0
            new_bb0_list = []
            for instruction in self.ir.bb_list[0].instruction_list:
                # the first instruction that exceeds pc
                if pc <= instruction.instruction_id < self.ir.pc:
                    continue
                else:
                    new_bb0_list.append(instruction)
            self.ir.bb_list[0].instruction_list = new_bb0_list
            self.ir.bb_list = self.ir.bb_list[:bb+1]
            self.ir.pc = pc
            self.ir.bb_count = bb
            self.next()
            # actual run of the while statement
            self.whileStatement(preRun=False, ssa_table_ahead=ssa_table_ahead)
        # "return"
        elif self.inputSym == 104:
            self.returnStatement()

    # "let" designator "<-" expression
    def assignment(self):
        self.checkFor(100)
        var = self.tokenizer.id
        operant, type, idx_table = self.designator(read=False)
        self.checkFor(40)
        val = self.expression()
        if type == "var":
            self.ir.setIdent(id = var, instruction_id = val)
        if type == "array":
            base_addr = operant[0]
            dimension = operant[1]
            offset_sum = None
            for idx, dim in enumerate(idx_table):
                if idx == 0:
                    offset_sum = dim
                    continue
                offset_sum =  self.ir.addInstruction("mul", operant1=offset_sum, operant2=dimension[idx]).instruction_id
                offset_sum =  self.ir.addInstruction("add", operant1=offset_sum, operant2=dim).instruction_id
            off_set = self.ir.addInstruction("mul", operant1=offset_sum, operant2=self.ir.immediate(4)).instruction_id
            base_addr = self.ir.addInstruction("add", "#BASE", base_addr).instruction_id
            addr = self.ir.addInstruction("adda", operant1=base_addr, operant2=off_set).instruction_id
            self.ir.addInstruction("store", operant1=addr, operant2=val).instruction_id

    # "call" ident [ "(" [expression { "," expression } ] ")" ]
    def funcCall(self):
        self.checkFor(101)
        function_name = self.tokenizer.id
        function_instruction = None
        if function_name == "InputNum":
            function_instruction = Instruction(instruction_id=-1, op_code="read")
        elif function_name == "OutputNum":
            # reserve instruction
            function_instruction = Instruction(instruction_id=-1, op_code="write", operant1=None)
        elif function_name == "OutputNewLine":
            function_instruction = Instruction(instruction_id=-1, op_code="writeNL")
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
                function_instruction.operant1 = self.expression()
                # ","
                while self.inputSym == 31:
                    self.checkFor(31)
                    self.expression()
                # matching closing parenthese
            self.checkFor(35)
            function_instruction.instruction_id = self.ir.pc
            self.ir.bb_list[self.ir.bb_count].instruction_list.append(function_instruction)
            self.ir.pc += 1
        # function without parentheses, no parameters allowed
        return function_instruction.instruction_id
    
    # "if" relation "then" statSequence [ "else" statSequence ] "fi"
    # create a branch bb, a fall through bb, a join bb
    def ifStatement(self):
        self.checkFor(102)
        base_branch_instruction = self.relation()
        parent_bb = self.ir.bb_list[self.ir.bb_count]

        # fall through
        self.checkFor(41)
        fall_through_bb = self.ir.addBB(fall_through=True)
        self.ir.addDominator(fall_through_bb, parent_bb)
        
        self.statSequence()
        # if more statement happend in statSequence
        # update fall through to the join block of fall throught
        fall_through_bb = self.ir.bb_list[self.ir.bb_count]
        # for the fall through block branching back to join block
        ft_branch_instruction = self.ir.addInstruction('bra', None)
        # optional "else" sequence, branch
        if self.inputSym == 90:
            # BUG FIX NUMBERING IF NEXT INSTRUCTION CONSTANT
            base_branch_instruction.operant2 = self.ir.pc
            branch_bb = self.ir.addBB(branch=True, parent=parent_bb)
            self.ir.addDominator(branch_bb, parent_bb)
            self.checkFor(90)
            self.statSequence()
            branch_bb = self.ir.bb_list[self.ir.bb_count]
            # join block
            join_bb = self.ir.addBB(fall_through=True, parent=branch_bb)
            self.ir.addDominator(join_bb, parent_bb)
            fall_through_bb.branch = join_bb
            #  BUG FIX NUMBERING IF NEXT INSTRUCTION CONSTANT
            fall_through_bb.instruction_list[-1].operant1 = self.ir.pc
            self.ir.addPhi(join_bb, branch_bb, fall_through_bb)
            self.ir.addDominator(branch_bb, parent_bb)
        # no else
        else:
            join_bb = self.ir.addBB(branch=True, parent=fall_through_bb)
            self.ir.addDominator(join_bb, parent_bb)
            #  BUG FIX NUMBERING IF NEXT INSTRUCTION CONSTANT
            base_branch_instruction.operant2 = self.ir.pc
            ft_branch_instruction.operant1 = self.ir.pc
            join_bb.parents = [fall_through_bb, parent_bb]
            parent_bb.branch = join_bb
            self.ir.addPhi(join_bb, parent_bb, fall_through_bb)
        self.checkFor(82)

    # "while" relateion "do" statSequence "od"
    def whileStatement(self, preRun = False, ssa_table_ahead = {}):
        # upstream bb and loop header
        base_bb = self.ir.bb_list[self.ir.bb_count]
        loop_header = self.ir.addBB(fall_through=True, parent=base_bb)
        if preRun:
            self.checkFor(103)
            # basically do nothing in preRun
            ssa_table_ahead = loop_header.ssa_table
        self.ir.reserveWhilePhi(loop_header, ssa_table_ahead)
        self.ir.addDominator(loop_header, base_bb)
        while_branch_instruction = self.relation()
        # fall-through loop body
        self.checkFor(42)
        loop_body = self.ir.addBB(fall_through=True, parent=loop_header)
        self.ir.addDominator(loop_body, loop_header)
        self.statSequence()
        loop_body = self.ir.bb_list[self.ir.bb_count]
        loop_body.branch = loop_header
        self.ir.addInstruction('bra', operant1=loop_header.instruction_list[0].instruction_id, target=loop_body)
        # self.ir.addPhi(loop_header, loop_body, loop_header)
        # follow
        self.checkFor(81)
        if not preRun:
            self.ir.updateWhilePhi(loop_header, loop_body)
        while_branch_instruction.operant2 = self.ir.pc
        follow_bb = self.ir.addBB(branch=True, parent=loop_header)
        self.ir.addDominator(follow_bb, loop_header)
        if preRun:
            return loop_body.ssa_table
    
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
    # if called from assignment, read = false
    # called elsewhere, read = True
    # combination read var, write var, read array, write array
    def designator(self, read: bool = True):
        operant = None
        if read:
            # get token from current block ssa table
            operant = self.ir.getIdent(self.tokenizer.id)
        self.checkFor(61)
        type = "var"
        # array load
        idx_table = []
        if self.inputSym == 32:
            type = "array"
            operant = self.ir.getIdent(self.tokenizer.id)
        while self.inputSym == 32:
            self.checkFor(32)
            idx_table.append(self.expression())
            self.checkFor(34)
        return operant, type, idx_table
    
    # designator|number|"(" expression ")"|funcCall
    # = designator = indent
    # = number
    # = "("...
    # = funcCall = "call"...
    def factor(self):
        operant = None
        if self.inputSym == 61:
            # find identifier in current block ssa or parent block ssa
            operant, type, idx_table = self.designator()
            if type == "array":
                base_addr = operant[0]
                dimension = operant[1]
                offset_sum = None
                for idx, dim in enumerate(idx_table):
                    if idx == 0:
                        offset_sum = dim
                        continue
                    offset_sum = self.ir.addInstruction("mul", operant1=offset_sum, operant2=dimension[idx]).instruction_id
                    offset_sum = self.ir.addInstruction("add", operant1=offset_sum, operant2=dim).instruction_id
                off_set = self.ir.addInstruction("mul", operant1=offset_sum, operant2=self.ir.immediate(4)).instruction_id
                base_addr = self.ir.addInstruction("add", "#BASE", base_addr).instruction_id
                addr = self.ir.addInstruction("adda", operant1=base_addr, operant2=off_set).instruction_id
                operant = self.ir.addInstruction("load", operant1=addr).instruction_id
        elif self.inputSym == 60:
            operant = self.ir.immediate(self.tokenizer.number)
            self.checkFor(60)
        elif self.inputSym == 50:
            self.checkFor(50)
            operant = self.expression()
            self.checkFor(35)
        elif self.inputSym == 101:
            operant = self.funcCall()
        else:
            raise Exception
        return operant
    
    # factor { ("*"|"/") factor}
    def term(self):
        op_code = None
        operant1 = self.factor()
        operant2 = None
        while self.inputSym == 1 or self.inputSym == 2:
            op_code = token_operator_map[self.inputSym]
            if self.inputSym == 1:
                self.checkFor(1)
            else:
                self.checkFor(2)
            operant2 = self.factor()
            operant1 = self.ir.addInstruction(op_code, operant1, operant2).instruction_id
        return operant1
    
    def expression(self):
        operant1 = self.term()
        operant2 = None
        op_code = None
        while self.inputSym == 11 or self.inputSym == 12:
            op_code = token_operator_map[self.inputSym]
            if self.inputSym == 11:
                self.checkFor(11)
            else:
                self.checkFor(12)
            operant2 = self.term()
            operant1 = self.ir.addInstruction(op_code, operant1, operant2).instruction_id
        return operant1

    # expression relOp expression
    def relation(self):
        operant1 = self.expression()
        operant2 = None
        op_code = None
        # if relation fall through
        # token  20:==,  21:!=,  22:<,  23:>=,  24:<=,  25:> 
        # if NOT relation branch
        # branch 'bne'   'beq'   'bge'  'blt'   'bgt'   'ble'
        branch_map = {20:'bne', 21:'beq', 22:'bge', 23:'blt', 24:'bgt', 25:'ble'}
        if self.inputSym in [20, 21, 22, 23, 24, 25]:
            op_code = self.inputSym
            self.checkFor(self.inputSym)
        else:
            raise Exception
        operant2 = self.expression()
        self.ir.addInstruction("cmp", operant1, operant2)
        return self.ir.addInstruction(branch_map[op_code], self.ir.pc-1, None)

def main():
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        # raise Exception
    else:
        filename = "sample0"
    # pass filename as argument
    parser = Parser(filename)
    # parser = Parser("source_code_input")
    parser.parse()
    parser.ir.toGraph()
    parser.ir.printSSA()


if __name__ == "__main__":
    main()