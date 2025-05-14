# Константа: скорость света (м/с)
C = 3e8

# Функции работы программы
def f0(Fif, dmax): return Fif * 3e8 / (2 * dmax)  # S
def f1(f0): return 3e8 / f0  # lambda_
def f2(lambda_, Tc): return lambda_ / (4 * Tc)  # vmax
def f3(B): return 3e8 / (2 * B)  # dres
def f4(B, Tc): return B / Tc  # S
def f5(N, Tc): return N * Tc  # Tf
def f6(lambda_, Tf): return lambda_ / (2 * Tf)  # vres
def f7(Fif, S): return Fif * 3e8 / (2 * S)  # dmax
def f8(lambda_): return 3e8 / lambda_  # f0
def f9(vmax, Tc): return vmax * 4 * Tc  # lambda_
def f10(lambda_, vmax): return lambda_ / (4 * vmax)  # Tc
def f11(dres): return 3e8 / (2 * dres)  # B
def f12(S, Tc): return S * Tc  # B
def f13(B, S): return B / S  # Tc
def f14(Tf, Tc): return int(Tf / Tc)  # N
def f15(Tf, N): return Tf / N  # Tc
def f16(vres, Tf): return vres * 2 * Tf  # lambda_
def f17(lambda_, vres): return lambda_ / (2 * vres)  # Tf
def f18(dmax, S): return dmax * 2 * S / 3e8  # Fif

flist = [
    [f0, "Fif", "dmax", "S", 0],  # S = Fif * 3e8 / (2 * dmax)
    [f1, "f0", None, "lambda_", 2],  # lambda_ = 3e8 / f0
    [f2, "lambda_", "Tc", "vmax", 0],  # vmax = lambda_ / (4 * Tc)
    [f3, "B", None, "dres", 2],  # dres = 3e8 / (2 * B)
    [f4, "B", "Tc", "S", 0],  # S = B / Tc
    [f5, "N", "Tc", "Tf", 0],  # Tf = N * Tc
    [f6, "lambda_", "Tf", "vres", 0],  # vres = lambda_ / (2 * Tf)
    [f7, "Fif", "S", "dmax", 0],  # dmax = Fif * 3e8 / (2 * S)
    [f8, "lambda_", None, "f0", 2],  # f0 = 3e8 / lambda_
    [f9, "vmax", "Tc", "lambda_", 0],  # lambda_ = vmax * 4 * Tc
    [f10, "lambda_", "vmax", "Tc", 0],  # Tc = lambda_ / (4 * vmax)
    [f11, "dres", None, "B", 2],  # B = 3e8 / (2 * dres)
    [f12, "S", "Tc", "B", 0],  # B = S * Tc
    [f13, "B", "S", "Tc", 0],  # Tc = B / S
    [f14, "Tf", "Tc", "N", 0],  # N = int(Tf / Tc)
    [f15, "Tf", "N", "Tc", 0],  # Tc = Tf / N
    [f16, "vres", "Tf", "lambda_", 0],  # lambda_ = vres * 2 * Tf
    [f17, "lambda_", "vres", "Tf", 0],  # Tf = lambda_ / (2 * vres)
    [f18, "dmax", "S", "Fif", 0]  # Fif = dmax * 2 * S / 3e8
]

def calculate_parameters(current_params, input_history, priorities):
    check_list = ["f0", "lambda_", "Tc", "B", "S", "N", "Tf", "Fif", "vmax", "dres", "vres", "dmax"]
    dynamic = []
    now_par = ""
    uform = []
    out_list = []
    for i in range(len(check_list)):
        out_list.append(current_params.get(check_list[i]))
    
    while len(input_history) != 0:
        dynamic.insert(0, input_history[0])
        input_history = input_history[1::]
        out_list[check_list.index(dynamic[0])] = current_params.get(dynamic[0])

        while len(dynamic) != 0:
            now_par = dynamic[0]
            dynamic = dynamic[1::]
            now_form = []
            for i in range(19):
                if (flist[i][3] == now_par) and not(i in uform):
                    now_form.append(i)

            for i in range(len(now_form)):
                if flist[now_form[i]][2] == None: #2 тип
                    flist[now_form[i]][4] = 2
                elif (out_list[check_list.index(flist[now_form[i]][2])] == None) and (out_list[check_list.index(flist[now_form[i]][1])] == None): # 1 тип
                    flist[now_form[i]][4] = 1
                elif (out_list[check_list.index(flist[now_form[i]][3])] != None) and (
                    out_list[check_list.index(flist[now_form[i]][2])] != None) and (
                    out_list[check_list.index(flist[now_form[i]][1])] != None):
                    flist[now_form[i]][4] = 4
                else: #3 тип
                    flist[now_form[i]][4] = 3

            for i in range(len(now_form)):
                if not((now_form[i]) in uform):
                    if flist[now_form[i]][4] == 1:
                        for s in range(len(flist)):
                            if (flist[now_form[i]][1] in flist[s]) and (
                                flist[now_form[i]][2] in flist[s]) and (
                                flist[now_form[i]][3] in flist[s]):
                                uform.append(s)

            for i in range(len(now_form)):
                if flist[now_form[i]][4] == 2:
                    if not((now_form[i]) in uform):
                        for j in range(len(flist)):
                            if ((now_par == flist[j][1]) and (
                                flist[now_form[i]][1] == flist[j][3])) and not(j in uform):
                                out_list[check_list.index(flist[j][3])] = flist[j][0](
                                    out_list[check_list.index(now_par)])
                                uform.append(now_form[i])
                                uform.append(j)
                                dynamic.append(flist[j][3])
                                break

            for i in range(len(now_form)):
                if flist[now_form[i]][4] == 3:
                    if not((now_form[i]) in uform):
                        if out_list[check_list.index(flist[now_form[i]][1])] == None:
                            for j in range(len(flist)):
                                if ((flist[now_form[i]][1]) == flist[j][3]) and (
                                    (flist[now_form[i]][2]) in flist[j]) and (
                                    (flist[now_form[i]][3]) in flist[j]) and not(j in uform):
                                    out_list[check_list.index(flist[now_form[i]][1])] = flist[j][0](
                                        out_list[check_list.index(flist[j][1])],
                                        out_list[check_list.index(flist[j][2])])
                                    for s in range(len(flist)):
                                        if ((flist[now_form[i]][1] in flist[s]) and (
                                            flist[now_form[i]][2] in flist[s]) and (
                                            flist[now_form[i]][3] in flist[s])):
                                            uform.append(s)
                                    dynamic.append(flist[now_form[i]][1])
                        else:
                            for j in range(len(flist)):
                                if ((flist[now_form[i]][2]) == flist[j][3]) and (
                                    (flist[now_form[i]][1]) in flist[j]) and (
                                    (flist[now_form[i]][3]) in flist[j]) and not(j in uform):
                                    out_list[check_list.index(flist[now_form[i]][2])] = flist[j][0](
                                        out_list[check_list.index(flist[j][1])],
                                        out_list[check_list.index(flist[j][2])])
                                    for s in range(len(flist)):
                                        if ((flist[now_form[i]][1] in flist[s]) and (
                                            flist[now_form[i]][2] in flist[s]) and (
                                            flist[now_form[i]][3] in flist[s])):
                                            uform.append(s)
                                    dynamic.append(flist[now_form[i]][2])

            for i in range(len(now_form)):
                if flist[now_form[i]][4] == 4:
                    if not((now_form[i]) in uform):
                        for j in range(len(priorities)):
                            if ((flist[now_form[i]][3]) in priorities[j]) and (
                                (flist[now_form[i]][2]) in priorities[j]) and (
                                (flist[now_form[i]][1]) in priorities[j]) and not(j in uform):
                                if priorities[j].index(now_par) == 2:
                                    out_list[check_list.index(priorities[j][1])] = None
                                else:
                                    out_list[check_list.index(priorities[j][2])] = None
                            
                        else:
                            if out_list[check_list.index(flist[now_form[i]][1])] == None:
                                for j in range(len(flist)):
                                    if ((flist[now_form[i]][1]) == flist[j][3]) and (
                                        (flist[now_form[i]][2]) in flist[j]) and (
                                        (flist[now_form[i]][3]) in flist[j]) and not(j in uform):
                                        out_list[check_list.index(flist[now_form[i]][1])] = flist[j][0](
                                            out_list[check_list.index(flist[j][1])],
                                            out_list[check_list.index(flist[j][2])])
                                        for s in range(len(flist)):
                                            if ((flist[now_form[i]][1] in flist[s]) and (
                                                flist[now_form[i]][2] in flist[s]) and (
                                                flist[now_form[i]][3] in flist[s])):
                                                uform.append(s)
                                    dynamic.append(flist[now_form[i]][1])
                            else:
                                for j in range(len(flist)):
                                    if ((flist[now_form[i]][2]) == flist[j][3]) and (
                                        (flist[now_form[i]][1]) in flist[j]) and (
                                        (flist[now_form[i]][3]) in flist[j]) and not(j in uform):
                                        out_list[check_list.index(flist[now_form[i]][2])] = flist[j][0](
                                            out_list[check_list.index(flist[j][1])],
                                            out_list[check_list.index(flist[j][2])])
                                        for s in range(len(flist)):
                                            if ((flist[now_form[i]][1] in flist[s]) and (
                                                flist[now_form[i]][2] in flist[s]) and (
                                                flist[now_form[i]][3] in flist[s])):
                                                uform.append(s)
                                        dynamic.append(flist[now_form[i]][2])

        for i in range(len(flist)):
            flist[i][4] = 0
        now_par = ""
        uform = []
        now_form = []

    return out_list

# Единицы измерения для параметров
UNITS = {
    'f0': 'GHz',    # ГГц
    'lambda_': 'm',  # м
    'Tc': 'ms',     # мс
    'B': 'GHz',     # ГГц
    'S': 'GHz/μs',  # ГГц/мкс
    'N': 'units',   # шт
    'Tf': 's',      # с
    'Fif': 'MHz',   # МГц
    'vmax': 'm/s',  # м/с
    'dres': 'm',    # м
    'vres': 'm/s',  # м/с
    'dmax': 'm',    # м
    'mem': 'MB'     # Мб
}

# Конверсия в единицы СИ
def convert_to_si(param, value):
    try:
        value = float(value)
        if param == 'f0' or param == 'B':
            return value * 1e9  # ГГц → Гц
        elif param == 'Tc':
            return value * 1e-3  # мс → с
        elif param == 'S':
            return value * 1e15  # ГГц/мкс → Гц/с
        elif param == 'Fif':
            return value * 1e6  # МГц → Гц
        elif param == 'mem':
            return value * 1e6  # Мб → байты
        return value  # м, м/с, шт, с
    except ValueError:
        return None