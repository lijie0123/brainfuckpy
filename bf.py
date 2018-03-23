"""
create by lijie at 2018/3/21
email : lijie0123lj@gmail.com
"""
def code_gen(s):
    lst = []
    stk = []
    for i in s:
        if i in ('+', '-', '<', '>', '.', ',', '!'):
            lst.append([i, None])
        elif i == '[':
            lst.append([i, None])
            stk.append(len(lst) - 1)
        elif i == ']':
            f = stk.pop()
            lst.append([i, f])
            lst[f][1] = len(lst)
        elif i in (' ', '\t', '\n'):
            pass
        else:
            raise ValueError
    if len(stk):
        raise ValueError
    return lst


import re

macdef = re.compile(r"\s*#([A-Za-z]\w*)\((.*?)\)\s*=\s*(.*)$")
macref = re.compile(r"#([A-Za-z]\w*)\((.*?)\)")
fundef = re.compile(r"\s*\$([A-Za-z]\w*)\((.*?)\):(.*)=\s*(.*)")
funcall = re.compile(r"\$([A-Za-z]\w*)\((.*?)\)")


def move(x):
    if x >= 0:
        return '>' * x
    else:
        return '<' * (-x)


def decrease_to_zero():
    return '[-]'


def add_from_now(x):
    return '[-' + move(x) + '+' + move(-x) + ']'


def copy_now_to_from_empty(now, to, frm, empt):
    to -= now
    frm -= now
    empt -= now
    s = move(to) + decrease_to_zero() + move(empt - to) + decrease_to_zero() + move(frm - empt) + '[-' + move(
        to - frm) + '+' + move(empt - to) + '+' + move(frm - empt) + ']' + move(empt - frm) + '[-' + move(
        frm - empt) + '+' + move(empt - frm) + ']' + move(-empt)
    return s


def copy_ptr(s, base):
    ret = ""
    for i in s:
        # ret += copy_now_to_from_empty(base, base+1, i, base+2)+'>'
        ret += '>[-]>[-]' + move(i - base - 2) + '[-' + move(base + 1 - i) + '+>+' + move(i - base - 2) + ']' + move(
            base + 2 - i) + '[-' + move(i - base - 2) + '+' + move(base + 2 - i) + ']<'
        base += 1
    return ret


def clean_params(funobj):
    return move(-funobj['params'])


def fun_def(funmap, name, params, ret, body):
    ob = {'name': name, 'params': params, 'ret': ret, 'body': body}
    funmap[name] = ob
    return ob


def mac_def(map, name, params, body):
    ob = {'name': name, 'params': params, 'body': body}
    map[name] = ob
    return ob


def fun_call(map, name, params):
    if (len(params) != map[name]['params']):
        raise Exception('parameter numbers not equal')
    s = move(map[name]['ret']) + copy_ptr(params, map[name]['ret'])
    s += map[name]['body']
    s += clean_params(map[name])
    return s


def macroprocessor(s):
    lst = s.splitlines(keepends=False)
    map = {}
    out = ""
    for l in lst:
        mat = macdef.match(l)
        if mat:
            name = mat.group(1)
            params = mat.group(2).strip().split(',')
            paramsc = 0
            for i in params:
                if i:
                    paramsc += 1

            body = mat.group(3)
            body = apply_mac(body, map)
            mac_def(map, name, paramsc, body)
            continue
        out += apply_mac(l, map) + '\n'
    return out


def func_processor(s):
    lst = s.splitlines(keepends=False)
    map = {}
    out = ""
    for l in lst:
        mat = fundef.match(l)
        if mat:
            name = mat.group(1)
            params = mat.group(2).strip().split(',')
            paramsc = 0
            for i in params:
                if i:
                    paramsc += 1
            ret = mat.group(3).strip().split(',')
            retc = 0
            for i in ret:
                retc += 1
            body = mat.group(4)
            body = apply_fun(body, map)
            fun_def(map, name, paramsc, retc, body)
            continue
        out += apply_fun(l, map)
    return out


def apply_mac(s, map):
    while True:
        refs = macref.findall(s)
        if not refs:
            break
        for it in refs:
            params = it[1].strip()
            if params == '':
                params = []
            else:
                params = [int(i) for i in params.split(',')]
            target = make_mac(map, it[0], params)
            s = s.replace("#%s(%s)" % it, target)
    return s


def make_mac(map, name, params):
    if name in map:
        return map[name]['body']
    if name == 'copy':
        if (len(params) != 3):
            raise Exception('Macro parameter not equal')
        return copy_now_to_from_empty(0, *params)
    if name == 'add_from_now':
        if (len(params) != 1):
            raise Exception('Macro parameter not equal')
        return add_from_now(params[0])
    if name == 'move':
        if (len(params) != 1):
            raise Exception('Macro parameter not equal')
        return move(params[0])
    if name == 'num':
        if (len(params) != 1):
            raise Exception('Macro parameter not equal')
        return r"[-]" + '+' * params[0]
    raise Exception('Macro not defined')


def apply_fun(s, map):
    while True:
        refs = funcall.findall(s)
        if not refs:
            break
        for it in refs:
            params = it[1].strip()
            if params == '':
                params = []
            else:
                params = [int(i) for i in params.split(',')]
            target = fun_call(map, it[0], params)
            s = s.replace("$%s(%s)" % it, target)
    return s


def bf_code(s):
    output = ""
    for i in s:
        if i in ('+', '-', '<', '>', '[', ']', '.', ',', '!'):
            output += i
    return output


def execute(s):
    try:
        s = pre_process(s)
        codes = code_gen(s)
    except Exception as e:
        raise Exception("Syntax error", e)
    try:
        posdata = [0] * 100
        negdata = [0] * 100
        data_ptr = 0
        PC = 0
        while PC < len(codes):
            if data_ptr >= 0 and len(posdata) < data_ptr + 1:
                posdata.extend((0 for i in range(data_ptr - len(posdata) + 1)))
            elif data_ptr < 0 and len(negdata) < (-data_ptr) + 1:
                negdata.extend((0 for i in range(-data_ptr - len(negdata) + 1)))
            ins = codes[PC]
            if ins[0] == '+':
                if data_ptr >= 0:
                    posdata[data_ptr] += 1
                else:
                    negdata[-data_ptr] += 1
            elif ins[0] == '-':
                if data_ptr >= 0:
                    posdata[data_ptr] -= 1
                else:
                    negdata[-data_ptr] -= 1
            elif ins[0] == '<':
                data_ptr -= 1
            elif ins[0] == '>':
                data_ptr += 1
            elif ins[0] == '[':
                if data_ptr >= 0 and not posdata[data_ptr]:
                    PC = ins[1]
                    continue
                elif data_ptr < 0 and not negdata[-data_ptr]:
                    PC = ins[1]
                    continue
            elif ins[0] == ']':
                PC = ins[1]
                continue
            elif ins[0] == '.':
                if data_ptr >= 0:
                    t = posdata[data_ptr]
                else:
                    t = negdata[-data_ptr]
                print(t)
            elif ins[0] == ',':
                t = int(input())
                if data_ptr >= 0:
                    posdata[data_ptr] = t
                else:
                    negdata[-data_ptr] = t
            elif ins[0] == '!':
                pass
            else:
                raise ValueError
            PC += 1
    except Exception as e:
        raise Exception("Runtime error", e)
    return None


preload = """
    #pop() = <
    $add(x,y):z = <<[-]>[-<+>]>[-<<+>>]
    $mns(x,y):z = <<[-]>>[-<->]<[-<+>]>
    $dup(x):z = <[-]>[-<+>]
    $mul(x,y):z = <<[-]>>>[-]<<[- #copy(3,1,4)  #move(3) #add_from_now(-1) #move(-3) ] #copy(-1,2,0) >
    
    """


def pre_process(s):
    s = preload + s
    s = macroprocessor(s)
    s = func_processor(s)
    s = bf_code(s)
    return s


if __name__ == "__main__":
    l = "#num(4) . > #num(6) . $add(0,-1) . $mul(0,-1) . $mns(0,-1) . $add(-1,-2) ."
    execute(l)
