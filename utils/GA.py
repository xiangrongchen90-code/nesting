import numpy as np
import matplotlib.pyplot as plt
import random
import time
from ezdxf.entities import LWPolyline
import math
import ezdxf
import random

# 交配完成後可能導致排片重複，本函式就是要讓他變成不重複
def order_repeat_fix(population_arr):
    # 取出排樣順序
    arr = population_arr[:(len(population_arr)//2)]
    # 取出旋轉角度
    arr2 = population_arr[(len(population_arr) // 2):]

    # 找出真正範圍與目前的差集
    # 例如 n=4，range 為 {0,1,2,3}，若 arr 為 [0,1,1,2]，差集就是 {3}(少了3)
    miss_number = list(set(range(len(arr))) - set(arr))

    # 隨機性
    random.shuffle(miss_number)

    # 紀錄已經出現過的數字
    number_record = set()

    # 逐一檢查陣列中的每個位置
    for i in range(len(arr)):
        # 如果當前數字已經在seen集合中，代表這是一個重複出現的元素
        if arr[i] in number_record:
            # 從遺失清單中彈出一個數字，取代掉重複的項
            arr[i] = miss_number.pop()
        else:
            # 如果是第一次見到的數字，就將它加入 seen 集合，作為後續比對的依據
            number_record.add(arr[i])

    return np.concatenate([arr, arr2])
# 測試用
#print(order_repeat_fix([0, 1, 1, 2,20,30,40,50]))

#設定初始值為30*2
def initial(part_len,industry = True):
    number=30
    x1 = np.array([
        np.random.permutation(part_len)  # 不重複排列
        for _ in range( number)
    ])
    if industry != 1 :
        x2 = np.random.choice(
            [0, 46, 90, 136, 180, 226, 270, 316],
            size=(number, part_len),
            p=[0.20, 0.05, 0.20, 0.05, 0.20, 0.05, 0.20, 0.05]
        )
    else:
        x2 = np.zeros((number, part_len), dtype=int)

    population = np.hstack((x1, x2))
    return population

#找前5名，另外5名用輪盤法找，共10名
def select(fit, pop):
    fit = np.array(fit)

    #選前5名
    good_value = []
    good_fit = []
    best_idx = np.argsort(fit)[:5]

    for idx in best_idx:
        good_value.append(pop[idx])
        good_fit.append(fit[idx])

    #準備輪盤法母體
    remain_fit = np.delete(fit, best_idx)
    remain_pop = [pop[i] for i in range(len(pop)) if i not in best_idx]

    # 輪盤法選5名
    remain_fit_adj = np.max(remain_fit) - remain_fit + 1e-6
    prob = remain_fit_adj / np.sum(remain_fit_adj)
    cum_prob = np.cumsum(prob)

    for _ in range(5):
        r = random.random()
        idx = np.where(cum_prob >= r)[0][0]
        good_value.append(remain_pop[idx])
        good_fit.append(remain_fit[idx])

    # 依適應值排序（由小到大）
    order = np.argsort(good_fit)
    good_value_sorted = [good_value[i] for i in order]
    print("最小適應值:",good_fit[order[0]])
    return good_value_sorted


#交配+突變
# 交配 + 突變
def crossover_mutation(
    parent1,
    parent2,
    part_len,
    industry=True,
    special_mode=False,
    forced_part=None
):
    child = parent2.copy()
    # Crossover（交配）
    if random.random() < 0.6:
        if special_mode:
            # 特殊排樣：
            # 樣片種類不進行交配
            # 只讓角度部分進行交配
            idx = random.randint(part_len, part_len * 2 - 1)
            child[idx:] = parent1[idx:]
        else:
            # 正常排樣：
            # 樣片 + 角度都可以交配
            idx = random.randint(0, part_len * 2 - 1)
            child[:idx] = parent1[:idx]
            # 修正樣片重複
            child = order_repeat_fix(child)
    else:
        # 不進行交配
        # 重新產生染色體
        if special_mode:
            # 特殊排樣：
            # 所有樣片強制使用目前要補的樣片
            order = np.full(
                part_len,
                forced_part,
                dtype=int
            )
        else:
            # 正常排樣
            order = np.random.permutation(part_len)
        # 產生角度
        if industry != 1:
            angle = np.random.choice(
                [0, 46, 90, 136, 180, 226, 270, 316],
                part_len,
                p=[
                    0.20, 0.05, 0.20, 0.05,
                    0.20, 0.05, 0.20, 0.05
                ]
            )
        else:
            angle = np.zeros(
                part_len,
                dtype=int
            )
        child = np.concatenate(
            [order, angle]
        )
    # Mutation（突變）
    if random.random() < 0.6:
        # 特殊排樣與正常排樣
        # 都只突變角度
        idx = random.randint(
            part_len,
            part_len * 2 - 1
        )
        if industry != 1:
            child[idx] = random.choices(
                [0, 46, 90, 136, 180, 226, 270, 316],
                weights=[
                    0.20, 0.05, 0.20, 0.05,
                    0.20, 0.05, 0.20, 0.05
                ],
                k=1
            )[0]
    # 特殊排樣最後保險
    if special_mode:

        # 確保樣片種類一定是 forced_part
        child[:part_len] = forced_part

    return child
# child = crossover_mutation([0,2,1,3,20,50,100,120], [1,2,0,3,120,150,10,120], 4,industry = False)
# print(child)
# part_len=4
# star_time=time.time()
# pop = initial(part_len)
# curve = []
# for i in range(10):
#     fit = fitness_value(pop[:,0],pop[:,1])
#     curve.append(fit[np.argmin(fit)])
#     good_value = select(fit.copy(),pop.copy())
#     for j in range(10):
#         for i in range(10):
#             child=crossover(good_value[j],good_value[i],part_len)
#             pop[10*j+i]=child
# fit=fitness_value(pop[:,0],pop[:,1])
# idx=np.argmin(fit)
# print(f"x1={pop[idx][0]},x2={pop[idx][1]},fitness={fit[idx]}")
# stop_time=time.time()
# print(f"用時:{(stop_time-star_time):.2}")
# plt.plot(curve)
# plt.xlabel("Iteration")
# plt.ylabel("Best Z")
# plt.title("GA Convergence Curve")
# plt.ylim(0, 10)
# plt.show()