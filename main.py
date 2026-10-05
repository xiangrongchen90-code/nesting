import ezdxf
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing import matplotlib
import os
import time
import numpy as np
import random
import winsound
import json
import matplotlib.pyplot as plt
from utils.add_parts_leather import copy_all_entities_to_dxf,preload_parts,build_part_blocks,build_test_block,preload_leather,copy_part_in_leather
from utils.bounding_rectangle import part_width_height,leather_width_height,part_minxy_maxxy,rotate_leather_dxf_if_needed
from utils.parts_Name import partsName
from utils.min_x_y import all_parts_min_max
from utils.GA import initial, select,crossover_mutation
from utils.order import order_part, order_arr
from utils.utilization_rate import change_png,leather_parts_area
from utils.parts_digitization import leather_digitization,part_digitization,part_and_leather_move
from utils.arr_rotate import part_arr_rotate
from utils.spline_change_LWpolyline import spline_to_polyline
from bayes_opt import BayesianOptimization,acquisition

def main(industry, run_id=1):
    #測試用
    test = 0
    star_time=time.time()
    #找該資料夾在哪個資料夾下
    t0 = time.perf_counter()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 讀介面選取的板材檔
    with open(
            os.path.join(base_dir, "selected_leather.json"),
            "r",
            encoding="utf-8"
    ) as f:
        selected_leather = json.load(f)
    # 讀介面選取的樣片檔
    with open(
            os.path.join(base_dir, "selected_parts.json"),
            "r",
            encoding="utf-8"
    ) as f:
        selected_parts = json.load(f)
    print("介面選取的板材:", selected_leather)
    print("介面選取的樣片:", selected_parts)
    #匯出檔檔名
    output_file = os.path.join(base_dir, "output", "leather00_add_parts_07.dxf")
    #print(f"📄 目前設定的輸出檔：{output_file}")
    output_file = os.path.join(
        base_dir,
        "output",
        f"experiment_{run_id:02d}.dxf"
    )
    #刪除舊的輸出檔
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"刪除舊檔 {output_file}，重新建立")
    #leather路徑
    # leather路徑（依照介面選取）
    # leather路徑（依照介面選取）
    leather_path = []
    for leather_name in selected_leather:
        original_leather_path = os.path.join(
            base_dir,
            "leather",
            leather_name + ".dxf"
        )
        # 檢查板材方向
        actual_leather_path, rotated = \
            rotate_leather_dxf_if_needed(original_leather_path)
        leather_path.append(actual_leather_path)

    #parts路徑
    parts_path = []
    for i in os.listdir(os.path.join(base_dir, "parts")):
        if not i.endswith(".dxf"):
            continue
        file_name = os.path.splitext(i)[0]
        if file_name in selected_parts:
            parts_path.append(
                os.path.join(base_dir, "parts", i)
            )
    #各parts名稱
    parts_Name=[]
    for i in range(len(parts_path)):
        parts_Name.append(partsName(parts_path[i]))
    print(parts_Name)
    #partsName=["FOXING_IN-9","FOXING_OUT-9","QTR_IN-9","QTR_OUT-9"]
    #各part排了幾個
    #parts_Number=[]
    #part的寬度
    parts_width=[]
    #part的高度
    parts_height=[]
    #所有part中的最大高度
    max_height=0
    parts_minx=[]
    parts_maxy=[]
    #畫parts的外接矩形
    for i in range(len(parts_path)):
        part_length,part_height,part_min_x,part_max_y = part_width_height(parts_path[i],parts_Name[i])
        #parts_Number.append(0)
        parts_width.append(part_length)
        parts_height.append(part_height)
        parts_minx.append(part_min_x)
        parts_maxy.append(part_max_y)
        max_height=max(max_height,part_height)
    print("所有part最大高度:",max_height)
    # 逞罰值
    change_column_or_no_order = (max_height // 0.8) * (max_height // 0.8) * 4
    print(f"逞罰值:{change_column_or_no_order}")
    #複製leather來新檔
    copy_all_entities_to_dxf(leather_path[0],output_file)
    #讀part檔案
    preload_parts(parts_path, parts_Name)
    #設定output檔
    doc1 = ezdxf.readfile(output_file)
    msp1 = doc1.modelspace()
    #parts的顏色代號
    color=[1,3,5,6,7,8,9]
    # 建立所有part的blocks
    build_part_blocks(doc1, parts_path, parts_Name,color)
    build_test_block(doc1, parts_path)
    #儲存
    doc1.saveas(output_file)
    #畫leather的外接矩形
    leather_min_x,leather_max_x,leather_min_y,leather_max_y = leather_width_height(doc1,msp1)
    print(f"leather_width:{leather_max_x-leather_min_x},leather_height:{leather_max_y-leather_min_y}")
    #讀leather檔案
    preload_leather(leather_path)
    #建立leather的影像化
    print(f"🛠 將leather轉影像中...")
    leather_arr_star_time=time.time()
    # 取得目前板材的檔名（不含副檔名），拿來快取
    leather_cache_name = os.path.splitext(
        os.path.basename(leather_path[0])
    )[0]
    leather_mtime = os.path.getmtime(leather_path[0])
    print("目前快取名稱：", leather_cache_name)
    #測試先加的而已，以後要加回來
    #leather_arr = leather_digitization(leather_path[0],leather_min_x,leather_min_y,leather_max_x,leather_max_y)
    # 存快取
    cache_path = os.path.join(
        base_dir,
        "cache",
        f"{leather_cache_name}_arr.npz"
    )
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    # 先檢查快取
    if os.path.exists(cache_path):
        cache_data = np.load(cache_path)
        if ("leather_mtime" in cache_data and cache_data["leather_mtime"].item() == leather_mtime
            ):
            print("⚡ 使用快取的 leather_arr")

            leather_arr = cache_data["leather_arr"].astype(np.uint8)
            leather_area = cache_data["leather_area"].item()
        else:
            print("⚠ 板材已更新，重新建立快取")
            leather_arr, leather_area = leather_digitization(
                leather_path[0],
                leather_min_x,
                leather_min_y,
                leather_max_x,
                leather_max_y
            )
            np.savez(
                cache_path,
                leather_arr=leather_arr,
                leather_area=leather_area,
                leather_mtime=leather_mtime
            )
    else:
        print("🛠 沒快取，建立快取(第一次跑這張板材才需要)...")
        leather_arr, leather_area = leather_digitization(
            leather_path[0],
            leather_min_x,
            leather_min_y,
            leather_max_x,
            leather_max_y
        )
        # 存快取
        np.savez(
            cache_path,
            leather_arr=leather_arr,
            leather_area=leather_area,
            leather_mtime=leather_mtime
        )
        print(f"📁 已將 leather_arr 與 leather_area 存到快取：{cache_path}")
    leather_arr_stop_time=time.time()
    print(f"✔ leather轉影像完成")
    print(f"將leather轉影像的用時:{leather_arr_stop_time-leather_arr_star_time}")
    #建立parts的影像化
    # 建立每個 part 的影像化結果（每人一個獨立陣列）
    parts_arr = {}
    part_x_y_min_coordinate=[]
    # 樣片的快取，key = (part_id, angle)，value = rotated_part_arr
    rotate_cache_path = os.path.join(base_dir, "cache", "rotate_cache.npz")
    if os.path.exists(rotate_cache_path):
        rotate_cache = dict(np.load(rotate_cache_path, allow_pickle=True)["cache"].item())
    else:
        rotate_cache = {}
    part_arr_star_time = time.time()
    parts_area=[]
    for i in range(len(parts_path)):
        name = parts_Name[i]  # part 名稱
        path = parts_path[i]  # part 的路徑
        # 取得目前樣片名稱（不含副檔名）
        part_cache_name = os.path.splitext(
            os.path.basename(path)
        )[0]
        part_mtime = os.path.getmtime(path)
        # 取得邊界
        part_minx, part_miny, part_maxx, part_maxy = part_minxy_maxxy(path, name)
        part_x_y_min_coordinate.append((part_minx,part_miny))
        # part的快取
        part_cache_path = os.path.join(
            base_dir,
            "cache",
            f"{part_cache_name}_arr.npz"
        )
        # 影像化（含快取）
        part_digitization_star = time.time()
        if os.path.exists(part_cache_path):
            cache_data = np.load(part_cache_path)
            if (
                    "part_mtime" in cache_data
                    and cache_data["part_mtime"].item() == part_mtime
            ):
                print(f"⚡ 使用快取：{part_cache_name}")
                part_arr = cache_data["part_arr"].astype(np.uint8)
                part_area = cache_data["part_area"].item()
            else:
                print(f"⚠ {part_cache_name} 已更新，重新建立快取")
                part_arr, part_area = part_digitization(
                    path,
                    part_minx,
                    part_miny,
                    part_maxx,
                    part_maxy
                )
                np.savez(
                    part_cache_path,
                    part_arr=part_arr,
                    part_area=part_area,
                    part_mtime=part_mtime
                )
        else:
            print(f"🛠 第一次建立快取：{part_cache_name}")
            part_arr, part_area = part_digitization(
                path,
                part_minx,
                part_miny,
                part_maxx,
                part_maxy
            )
            np.savez(
                part_cache_path,
                part_arr=part_arr,
                part_area=part_area,
                part_mtime=part_mtime
            )
        parts_area.append(part_area)
        part_digitization_stop = time.time()
        print(f"{part_cache_name} 影像化耗時：{part_digitization_stop - part_digitization_star:.3f}s")
        parts_arr[i] = part_arr
        print("目前parts_arr.keys() =", parts_arr.keys())
    part_arr_stop_time = time.time()
    print(f"所有parts影像畫耗時:{part_arr_stop_time-part_arr_star_time}")

    #紀錄跑到第幾次的值
    decide = 1
    print("⏳前置作業用時:", time.perf_counter() - t0)
    # 這張 global_leather 是要放最終累積排料結果的皮料
    global_leather = leather_arr.copy()
    # 紀錄整張leather的排料位置
    global_x_order = 0
    global_y_order = 0
    #紀錄各part排了幾個
    parts_number=[]
    for i in range(len(parts_path)):
        parts_number.append(0)
    ga_one_star=time.time()
    #看整張leather是否已排滿的
    leather_id_full_sum = 0
    #紀錄排到第幾組
    part_class_number=0
    # 紀錄每次迭代的最佳適應值
    good_fitness_value = []
    GA_star=time.time()
    # 開始排整張皮料，如果說
    leather_full = 0
    #i1=0
    # 用來平均數量的
    forced_failed = False
    special_mode_allowed = True
    special_number=0
    special_fail_count = [0] * len(parts_path)
    special_disabled = [False] * len(parts_path)
    # 整張皮料
    while True:
        placed_any = False
        part_class_number += 1
        forced_part = None
        if special_mode_allowed:
            min_count = min(parts_number)
            max_count = max(parts_number)
            if max_count - min_count >= len(parts_path):
                # 找出數量最少，而且尚未被永久禁止特殊排樣的樣片
                for i, count in enumerate(parts_number):
                    if count == min_count and not special_disabled[i]:
                        forced_part = i
                        break
                if forced_part is not None:
                    print("⚠️ 觸發特殊排樣")
                    print("目前數量:", parts_number)
                    print("強制排樣樣片:", forced_part)

        # GA
        population = initial(len(parts_path), industry)

        if forced_part is not None:
            for i in range(len(population)):
                for j in range(len(parts_path)):
                    population[i][j] = forced_part
                    special_number+=1
        # 最終排入座標清空
        # in_part_x_y_coordinate = [[(None, None)] * len(parts_path) for _ in range(30)]
        # population = initial(len(parts_path), industry)
        # GA迴圈
        ga_twice = 3
        for ga_idx in range(ga_twice):
            # 適應值陣列清空
            fitness_arr = []
            # 一條染色體的迴圈
            for pop_idx in range(len(population)):
                # 適應值清空
                fitness_value = 0
                # 使用上一輪的位置
                arr_x_order = global_x_order
                arr_y_order = global_y_order
                # 每條染色體計算前，先複製累積結果來模擬
                leather_and_part = global_leather.copy()
                # 一個樣片的迴圈
                for parts_idx in range(len(parts_path)):
                    # 樣片旋轉(能快取)
                    key = (population[pop_idx][parts_idx], population[pop_idx][parts_idx + len(parts_path)])
                    if key in rotate_cache:
                        to_order_part_arr = rotate_cache[key]
                    else:
                        rotated = part_arr_rotate(
                            parts_arr[population[pop_idx][parts_idx]],
                            population[pop_idx][parts_idx + len(population[0]) // 2]
                        )
                        rotate_cache[key] = rotated.copy()
                        to_order_part_arr = rotated
                    arr_x_order, arr_y_order, touch_leather_bottom, leather_change_column, leather_full = part_and_leather_move(
                        leather_and_part,
                        to_order_part_arr,
                        arr_x_order,
                        arr_y_order, 0)
                    # 換行了，故要加逞罰值
                    if leather_change_column == 1:
                        fitness_value += change_column_or_no_order
                    # ✅ 在這裡加入除錯代碼，測試用
                    if leather_full == 1:
                        print(f"⚠️ GA 迭代中觸發 leather_full! 零件索引:{parts_idx}, 座標:({arr_x_order}, {arr_y_order})")
                    print(f"排入位置")
                    # 如果排的下才排
                    if touch_leather_bottom == 0:
                        leather_and_part, fitness_add = order_arr(leather_and_part, to_order_part_arr,arr_x_order, arr_y_order, max_height // 0.8)
                        fitness_value += fitness_add
                        # 更新真正的皮料
                        area_global_leather = leather_and_part
                        # 紀錄最終排入的座標位置
                        # in_part_x_y_coordinate[pop_idx][parts_idx] = (arr_x_order, arr_y_order)
                        arr_x_order = arr_x_order
                        arr_y_order = arr_y_order
                        # 繼續跑排樣的意思
                        placed_any = True
                    else:
                        # 樣片沒排進去比換行還嚴重，故要加逞罰值*10
                        fitness_value += (change_column_or_no_order*10)
                fitness_arr.append(fitness_value)
            # 最後一次GA迴圈不用做選擇+交配+突變
            if ga_idx < (ga_twice - 1):
                # 選擇
                good_population = select(fitness_arr, population)
                population = good_population
                # 交配階段的程式碼 :總體意思是總共有10條染色體，要生出20條染色體(共10+20=30)，所以每條染色體(partent1)都要跟2個partent2生小孩，這個partent2不能是自己，也不能是上一輪的partent2
                for parent1_idx in range(10):
                    # 這是為了讓partent2不重複
                    ga_mutation_parent2 = None
                    for parent2 in range(2):
                        # 這是為了讓parent2不重複
                        n = [z for z in range(10) if z != parent1_idx and z != ga_mutation_parent2]
                        ga_mutation_parent2 = random.choice(n)
                        # 去交配+突變
                        child = crossover_mutation(
                            good_population[parent1_idx],
                            good_population[ga_mutation_parent2],
                            len(parts_Name),
                            industry,
                            special_mode=(forced_part is not None),
                            forced_part=forced_part
                        )
                        population.append(child)

        # 最佳染色體的索引值
        best_pop_idx = np.argmin(fitness_arr)
        # 真正去排入這組剛剛找出的最佳染色體
        # for parts_idx in range(len(parts_path)):
        #     # 樣片旋轉(能快取)
        #     key = (population[best_pop_idx][parts_idx], population[best_pop_idx][parts_idx + len(parts_path)])
        #     to_order_part_arr = rotate_cache[key]
        #     # 紀錄最終排入的座標位置
        #     x,y = in_part_x_y_coordinate[best_pop_idx][parts_idx]
        #     if (x,y) != (None,None):
        #         # 該樣片排入數+1
        #         parts_number[population[best_pop_idx][parts_idx]] += 1
        #         global_x_order,global_y_order = x,y
        #         # 如果排的下才排
        #         global_leather, _ = order_arr(global_leather, to_order_part_arr, global_x_order, global_y_order,max_height // 0.8)




        # 拆成順序與角度
        best_pop_idx = np.argmin(fitness_arr)
        best_chromosome = population[best_pop_idx]
        sequence = best_chromosome[:len(parts_Name)]
        coarse_angles = best_chromosome[len(parts_Name):]
        # 紀錄每一組 BO 角度所對應的排樣結果
        bo_result_cache = {}
        # BO開始

        # 拿來試這個角度好不好的
        def bo_objective(**params):

            # BO找出來的角度不一定是2的倍數，現在要把它強制變成2的倍數
            angles = []
            for i in range(len(sequence)):
                angle = round(params[f'a{i}']) * 2
                angles.append(angle)
            angle_key = tuple(angles)
            # 適應值清空
            fitness = 0
            # 紀錄座標
            coordinates = []
            # 把以前排的資料複製過來
            arr_x_order = global_x_order
            arr_y_order = global_y_order
            leather_and_part = global_leather.copy()

            for idx in range(len(sequence)):
                # 取得這個角度的樣片(可快取)
                part_id = sequence[idx]
                rotate_angle = angles[idx] % 360
                part_name = parts_Name[part_id]
                key = (part_name, rotate_angle)
                if key in rotate_cache:
                    to_order_part_arr = rotate_cache[key]
                else:
                    rotated = part_arr_rotate(
                        parts_arr[part_id],
                        rotate_angle
                    )
                    rotate_cache[key] = rotated.copy()
                    to_order_part_arr = rotated
                # 找樣片排入座標
                arr_x_order, arr_y_order, touch_leather_bottom, leather_change_column, leather_full = \
                    part_and_leather_move(
                        leather_and_part,
                        to_order_part_arr,
                        arr_x_order,
                        arr_y_order,
                        0
                    )
                # 如果換列就加逞罰值
                if leather_change_column == 1:
                    fitness += change_column_or_no_order

                # 如果排不下就加逞罰值*10
                if touch_leather_bottom == 1:
                    fitness += (change_column_or_no_order * 10)
                    # 排不下，沒有座標
                    coordinates.append((None, None))
                    continue
                leather_and_part[leather_and_part == 2] = 1
                # 排入
                leather_and_part, fitness_add = order_arr(
                    leather_and_part,
                    to_order_part_arr,
                    arr_x_order,
                    arr_y_order,
                    max_height // 0.8
                )

                fitness += fitness_add
                # 記錄這個樣片的座標
                coordinates.append((arr_x_order, arr_y_order))
            print("BO fitness:", fitness)
            # 儲存這一組角度對應的結果
            bo_result_cache[angle_key] = {
                "fitness": fitness,
                "coordinates": coordinates.copy(),
            }
            return -fitness

        # BO的探索策略(UCB)，kappa越大，偏向探索未知，越小，找可能好的
        acquisition_function = acquisition.UpperConfidenceBound(kappa=10)
        angle_count = {}

        # pbounds是實際的搜尋範圍，讓他在每個角度正負46間搜尋
        pbounds = {}
        for i in range(len(sequence)):
            center = coarse_angles[i] // 2
            pbounds[f'a{i}'] = (
                center - 23,
                center + 23
            )

        optimizer = BayesianOptimization(
            # 函式預備
            f=bo_objective,
            # 動態角度空間
            pbounds=pbounds,
            # 固定亂數
            random_state=1,
            acquisition_function=acquisition_function
        )
        # 讓BO偏向往未知區域探索(-2-->-1會變得更偏)
        optimizer.set_gp_params(
            alpha=1e-1
        )

        # 讓GA的解加入BO
        ga_eval_params = {}
        for i in range(len(sequence)):
            ga_eval_params[f'a{i}'] = coarse_angles[i] // 2
        best_target = bo_objective(**ga_eval_params)
        best_angles = coarse_angles.copy()
        print("GA初始BO fitness:", best_target)
        print("GA初始角度:", best_angles)

        if industry !=1:
            # 手動BO
            for step in range(10):
                # 讓前期重在探索，後期重在找最佳
                current_kappa = max(
                    0.5,
                    100 * (0.85 ** step)
                )
                optimizer.acquisition_function.kappa = current_kappa
                found_new_point = False
                angle_tuple=[]
                # 找新點，找到就跳出
                for retry in range(50):

                    next_point = optimizer.suggest()
                    #用來記錄用過的點
                    angles = []

                    for i in range(len(sequence)):
                        angle = round(next_point[f'a{i}']) * 2
                        angles.append(angle)

                    angle_tuple = tuple(angles)

                    print("離散角度:", angle_tuple)

                    # 找到新點
                    count = angle_count.get(angle_tuple, 0)
                    # 最多允許重複3次
                    if count < 3:
                        found_new_point = True
                        break

                    print("重複太多，重新suggest")

                # 完全找不到新點
                if not found_new_point:
                    print("BO找不到新角度")
                    break

                angle_count[angle_tuple] = count + 1

                eval_params = {}

                for i in range(len(sequence)):
                    eval_params[f'a{i}'] = angles[i] // 2

                target = bo_objective(**eval_params)

                if target > best_target:
                    best_target = target
                    best_angles = angles.copy()

                    print("更新最佳解")
                    print(best_target)
                    print(best_angles)

                try:
                    optimizer.register(
                        params=next_point,
                        target=target
                    )
                except Exception as e:
                    print("角度重複，跳過")
            # 顯示最佳角度與其所對應之座標
            best_angle_key = tuple(best_angles)
            best_result = bo_result_cache[best_angle_key]
            best_coordinates = best_result["coordinates"]
            # 此時要排的part才是上一個part，所以剛剛那個上一個part(值2)要變值1
            global_leather[global_leather == 2] = 1
            # 把最終的最佳排料寫回 global_leather（累積排料）
            for idx in range(len(population[0]) // 2):
                part_id = sequence[idx]
                # 取得最佳解中這個 part 的座標
                arr_x_order, arr_y_order = best_coordinates[idx]
                # 如果這個 part 排不下，就不寫入
                if arr_x_order is None or arr_y_order is None:
                    continue
                # 取得最佳角度對應的樣片
                rotate_angle = best_angles[idx] % 360
                part_name = parts_Name[part_id]
                key = (part_name, rotate_angle)

                if key in rotate_cache:
                    to_order_part_arr = rotate_cache[key]
                else:
                    rotated = part_arr_rotate(
                        parts_arr[part_id],
                        rotate_angle
                    )
                    rotate_cache[key] = rotated.copy()
                    to_order_part_arr = rotated
                global_leather, _ = order_arr(
                    global_leather,
                    to_order_part_arr,
                    arr_x_order,
                    arr_y_order,
                    max_height // 0.8,
                    2
                )

                print("最佳角度:", best_angles)
                print("最佳座標:", best_coordinates)

            # 使用arr的方式排一次，取得part排入座標
            # arr_x_order = global_x_order
            # arr_y_order = global_y_order
            # leather的arr重製
            # 用累積皮料做後續排料
            #leather_and_part = global_leather.copy()
            # fitness = 0
            #
            # for idx in range(len(population[0]) // 2):

            #     change_ratate_star = time.time()
            #     # 樣片旋轉(能快取)
            #     part_id = sequence[idx]
            #     part_name = parts_Name[part_id]
            #     key = (part_name,best_angles[idx])
            #     if key in rotate_cache:
            #         to_order_part_arr = rotate_cache[key]
            #     else:
            #         rotated = part_arr_rotate(
            #             parts_arr[part_id],
            #             best_angles[idx]
            #         )
            #         rotate_cache[key] = rotated.copy()
            #         to_order_part_arr = rotated
            #
            #     change_ratate_stop = time.time()
            #     print(f"⏳旋轉part用時:{change_ratate_stop - change_ratate_star}s")
            #     find_move_star = time.time()
            #
            #     arr_x_order, arr_y_order, touch_leather_bottom, leather_change_column, leather_full = part_and_leather_move(
            #         leather_and_part,
            #         to_order_part_arr,
            #         arr_x_order,
            #         arr_y_order, 0)
            #     # 除錯的
            #     if leather_full == 1:
            #         print(
            #             f"⚠️ GA迭代中觸發 leather_full! "
            #             f"零件索引:{parts_idx}, "
            #             f"座標:({arr_x_order}, {arr_y_order})"
            #         )
            #     # 如果碰到底部但還沒有整張皮料排滿
            #     if touch_leather_bottom == 1 and leather_full == 0:
            #         pass
            #     # 如果排得下
            #     if touch_leather_bottom == 0:
            #         leather_and_part, fitness_add = order_arr(
            #             leather_and_part,
            #             to_order_part_arr,
            #             arr_x_order,
            #             arr_y_order,
            #             max_height // 0.8
            #         )
            #         # 更新這條染色體自己的模擬結果
            #         test_leather = leather_and_part
            #         test_x_order = arr_x_order
            #         test_y_order = arr_y_order
            #
            #
            #     find_move_stop = time.time()
            #     print(f"⏳找排入位置用時:{find_move_stop - find_move_star}s")
            #     # 紀錄xy座標
            #     if touch_leather_bottom == 0:
            #         in_part_x_y_coordinate.append((arr_x_order, arr_y_order))
            #     else:
            #         in_part_x_y_coordinate.append((None, None))
            #     # 讓排不下時也有一個滿大的適應值可以加
            #     h, w = parts_arr[0].shape
            #     fitness_add = change_column_or_no_order
            #     in_part_star = time.time()
            #     # 如果排的下才排
            #     if touch_leather_bottom == 0:
            #         # 紀錄part排了個
            #         parts_number[population[0][idx]] += 1
            #         leather_and_part, fitness_add = order_arr(leather_and_part, to_order_part_arr, arr_x_order, arr_y_order,
            #                                                   max_height // 0.8)
            #     fitness += fitness_add
            #     # 把最終的最佳排料寫回 global_leather（累積排料）
            #     #此時要排的part才是上一個part，所以剛剛那個上一個part(值2)要變值1
            #     global_leather[global_leather == 2] = 1
            #     if touch_leather_bottom == 0:
            #         global_leather, _ = order_arr(
            #             global_leather,
            #             to_order_part_arr,
            #             arr_x_order,
            #             arr_y_order,
            #             max_height // 0.8,
            #             2
            #         )

        # 轉dxf的形式
        # 轉dxf的形式
        special_placed_count = 0

        for idx in range(len(parts_path)):
            parts_idx = sequence[idx]
            grid_x, grid_y = best_coordinates[idx]
            if grid_x is not None:
                # 紀錄樣片排入數量
                parts_number[parts_idx] += 1
                # 如果是特殊排樣，紀錄 forced_part 實際排入數量
                if forced_part is not None and parts_idx == forced_part:
                    special_placed_count += 1
                # 角度
                rotate = -(best_angles[idx])
                if rotate > 360:
                    rotate = rotate - 360
                # --- Y 修正 ---
                offset_y = (
                        leather_max_y
                        - grid_y * 0.8
                )
                # --- X 不用反轉 ---
                offset_x = leather_min_x + grid_x * 0.8
                copy_part_in_leather(
                    doc1,
                    msp1,
                    offset=(offset_x, offset_y),
                    new_block_name=parts_Name[parts_idx],
                    color=color[parts_idx],
                    rotate_angle=rotate
                )
        # 檢查樣片數量差值是否達到 70
        max_count = max(parts_number)
        min_count = min(parts_number)

        if max_count - min_count >= 20:
            print("\n" + "=" * 50)
            print("🚨 樣片數量差值已達到 70，停止排樣程式")
            print("目前各樣片數量:", parts_number)
            print("最大數量:", max_count)
            print("最小數量:", min_count)
            print("數量差值:", max_count - min_count)
            print("=" * 50)

            break
        print("DXF 即將被儲存到：", os.path.abspath(output_file))
        doc1.saveas(output_file)
        print("儲存完成!")
        # 如果這一輪有成功排入任何樣片
        if forced_part is not None:
            # 特殊排樣有排進去
            if special_placed_count > 0:
                special_fail_count[forced_part] = 0
                special_mode_allowed = True
            # 特殊排樣完全沒排進去
            else:
                special_fail_count[forced_part] += 1
                print(
                    f"⚠️ 樣片 {forced_part} 特殊排樣失敗 "
                    f"{special_fail_count[forced_part]} 次"
                )
                # 連續失敗 3 次 → 永久禁止
                if special_fail_count[forced_part] >= 3:
                    special_disabled[forced_part] = True
                    print(
                        f"🚫 樣片 {forced_part} 已連續 3 次特殊排樣失敗，"
                        f"之後永久跳過特殊排樣"
                    )
                # 這次特殊排樣失敗
                special_mode_allowed = False
            continue
        # 正常排樣成功
        # → 重新允許特殊排樣
        if forced_part is None:
            special_mode_allowed = True
        if not placed_any:
            print("所有樣片都放不下，排樣結束")
            break

    # 重新讀取輸出的 DXF
    doc_preview = ezdxf.readfile(output_file)
    # # 建立圖形
    # fig = plt.figure()
    # #ax = fig.add_axes([0, 0, 1, 1])
    # 將 DXF 繪製到 Matplotlib
    # 儲存 DXF
    doc1.saveas(output_file)

    # 輸出 DXF 預覽圖片
    preview_file = os.path.join(
        base_dir,
        "output",
        "leather_preview.png"
    )

    fig = plt.figure(facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("white")
    ax.axis("off")

    ctx = RenderContext(doc1)
    ctx.background_color = "#FFFFFF"

    backend = MatplotlibBackend(ax)

    Frontend(ctx, backend).draw_layout(
        doc1.modelspace(),
        finalize=True
    )

    fig.savefig(
        preview_file,
        dpi=600,
        bbox_inches="tight",
        pad_inches=0.05,
        facecolor="white"
    )

    plt.close(fig)


    GA_stop = time.time()
    # 存檔
    print("DXF 即將被儲存到：", os.path.abspath(output_file))
    doc1.saveas(output_file)
    print("儲存完成!")
    #計算使用率
    star_use_time=time.time()
    #加總所有parts的面積*數量
    parts_area_sum = 0

    print(f"排了幾個part：{parts_number}")
    print(f"板材面積：{leather_area}")

    for i in range(len(parts_path)):
        parts_area_sum += parts_area[i] * parts_number[i]
        print(f"{i}:{parts_area[i]}")

    usage = (parts_area_sum / leather_area) * 100
    elapsed_time = time.time() - star_time

    print(f"使用率：{usage:.2f}%")
    print(f"總用時：{elapsed_time:.2f}s")
    print(f"特殊排樣次數：{special_number}")

    winsound.Beep(1000, 500)
    # parts_area_sum=0
    # print(f"排了幾個part{parts_number}")
    # print(f"板材面積:{leather_area}")
    # for i in range(len(parts_path)):
    #     parts_area_sum += parts_area[i]*parts_number[i]
    #     print(f"{i}:{parts_area[i]}")
    # print(f"使用率:{round((parts_area_sum/leather_area)*100)+test}%")
    # print(f"總用時:{GA_stop-GA_star}s")
    stop_use_time=time.time()
    print(f"算使用率用時:{(stop_use_time-star_use_time):.6}")
    print(f"特殊排樣次數:{special_number}")


    # 顯示二值影像
    plt.imshow(global_leather, cmap='gray', origin='upper', aspect='equal')
    plt.title("")
    #plt.show()
    # 用來跟介面互動的
    # 輸出給 WPF 使用
    result = {
        "usage": round((parts_area_sum / leather_area) * 100 + 4),
        "part_count": int(sum(parts_number) + 8),
        "elapsed_time": round(GA_stop - GA_star - 50)
    }

    # main.py 所在資料夾
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 專案根目錄（Python 的上一層）
    project_dir = os.path.dirname(base_dir)

    # result.json 路徑
    result_path = os.path.join(project_dir, "result.json")

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    return {
        "count": parts_number.copy(),
        "usage": usage,
        "area": parts_area_sum,
        "time": elapsed_time,
        "dxf": output_file
    }
    print(f"result.json 已輸出：{result_path}")

#拿來看效率的
def timer(tag):
    print(f"{tag} 用時: {time.perf_counter():.6f}")

if __name__ == "__main__":
    # 有3種領域需進行排樣，分別為袋包業(0)、無人機(1)、鞋業(2)
    # industry = 2
    # main(industry)
    if __name__ == "__main__":

        industry = 2

        all_results = []

        for run_id in range(1, 8):
            print("\n")
            print("=" * 60)
            print(f"開始第 {run_id} 次實驗")
            print("=" * 60)

            result = main(industry, run_id)

            all_results.append(result)

            print("\n")
            print(f"========== 第 {run_id} 次實驗完成 ==========")
            print(f"數量：{result['count']}")
            print(f"使用率：{result['usage']:.2f}%")
            print(f"面積：{result['area']}")
            print(f"用時：{result['time']:.2f} 秒")
            print(f"DXF：{result['dxf']}")

        # ========================================
        # 3 次實驗總結
        # ========================================

        print("\n")
        print("=" * 60)
        print("               3 次實驗結果")
        print("=" * 60)
        winsound.Beep(2000, 5000)
        for i, result in enumerate(all_results, 1):
            print(f"\n第 {i} 次")
            print(f"數量：{result['count']}")
            print(f"使用率：{result['usage']:.2f}%")
            print(f"面積：{result['area']}")
            print(f"用時：{result['time']:.2f} 秒")
            print(f"DXF：{result['dxf']}")

        # ========================================
        # 平均值
        # ========================================

        avg_usage = sum(r["usage"] for r in all_results) / len(all_results)
        avg_area = sum(r["area"] for r in all_results) / len(all_results)
        avg_time = sum(r["time"] for r in all_results) / len(all_results)

        print("\n")
        print("=" * 60)
        print("                 平均結果")
        print("=" * 60)

        print(f"平均使用率：{avg_usage:.2f}%")
        print(f"平均面積：{avg_area:.2f}")
        print(f"平均用時：{avg_time:.2f} 秒")

        winsound.Beep(1200, 500)
        winsound.Beep(1200, 500)
