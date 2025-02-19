import random
import os
import json

def gen_request(NUM_OF_NODES = 55, start_from_0=True, single_start=True, small_weihgt=True):
    """
    Tạo một yêu cầu giao hàng ngẫu nhiên với thông tin về điểm lấy hàng, điểm giao hàng,
    trọng lượng, ngày giao, và khung giờ giao hàng.

    Parameters:
    -----------
    single_start : bool, optional (default=True)
        - Nếu True, chỉ có một điểm lấy hàng.
        - Nếu False, số điểm lấy hàng có thể lên đến 4.

    small_weihgt : bool, optional (default=True)
        - Nếu True, trọng lượng của đơn hàng sẽ nhỏ (0 - 3 kg).
        - Nếu False, trọng lượng sẽ lớn hơn (12 - 30 kg).
        - Nếu giá trị khác True/False, trọng lượng nằm trong khoảng trung bình (7 - 20 kg).

    Returns:
    --------
    list
        - start_place (list): Danh sách các điểm lấy hàng (giá trị từ 0 đến 3).
        - end_place (list): Một điểm giao hàng duy nhất (giá trị từ 4 đến 53).
        - weight (float): Trọng lượng của đơn hàng (kg).
        - gen_day (int): Ngày giao hàng (0 đến 3).
        - gen_timeframe (list): Danh sách chứa hai giá trị thời gian giao hàng ngẫu nhiên trong ngày (0 đến 23 giờ).

    Example:
    --------
    >>> gen_request(single_start=False, small_weihgt=False)
    [[1, 2], [10], 15.3, 2, [3, 20]]
    """
    start_place = [0] if start_from_0 else random.sample([0, 1, 2, 3], k=random.randint(1, 1 if single_start else 4))
    end_place = random.sample(list(range(1, NUM_OF_NODES)), k=1)
    weight = random.randint(0*10, int(9.7*10))/10 if small_weihgt==True else random.randint(54*10, 300*10)/10 if small_weihgt==False else random.randint(24*10, 150*10)/10
    gen_day = random.randint(0, 3)
    gen_timeframe = sorted(random.sample(list(range(0, 24)), k=2))
    return [start_place, end_place, weight, gen_day, gen_timeframe]

def gen_requests_and_save(num_requests=10, file_sufices="", NUM_OF_NODES=55, start_from_0=True, seed=42):
    """
    Tạo một số lượng yêu cầu giao hàng ngẫu nhiên và lưu vào tệp CSV.

    Parameters:
    -----------
    num_requests : int, optional (default=10)
        - Số lượng yêu cầu giao hàng cần tạo.

    file_suffix : str, optional (default="")
        - Hậu tố được thêm vào tên tệp JSON. 
        - Nếu không cung cấp, tệp sẽ có tên mặc định là "requests.json".
        - Nếu cung cấp, tệp sẽ có dạng "requests<file_suffix>.json".

    Returns:
    --------
    requests: list
        - Danh sách các yêu cầu giao hàng được tạo, mỗi yêu cầu có định dạng giống như kết quả của `gen_request()`.

    Notes:
    ------
    - Hàm này sẽ tạo một tệp JSON có tên "requests<file_suffix>.json".
    - Nếu tệp đã tồn tại, nội dung sẽ bị ghi đè.
    - Mỗi hàng trong tệp JSON sẽ có định dạng:
      Start Place, End Place, Weight, Gen Day, Gen Timeframe

    Example:
    --------
    >>> requests = gen_requests_and_save(num_requests=5, file_suffix="_test")
    >>> print(requests)
    [[[0], [8], 2.1, 1, [3, 15]], ..., [[2], [27], 1.8, 3, [6, 19]]]

    - File CSV được tạo sẽ có tên "requests_test.csv".
    """
    random.seed(seed)

    requests = [gen_request(NUM_OF_NODES=NUM_OF_NODES, start_from_0=start_from_0) for i in range(num_requests*2)]
    have_request = [0 for i in range(NUM_OF_NODES)]
    filtered_requests = []
    for u in requests:
        if have_request[u[1][0]]:
            continue
        have_request[u[1][0]] = 1
        filtered_requests.append(u)
    requests = filtered_requests[:num_requests]

    # Determine the absolute path of the current file (in utilities)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate up one directory to get the project root
    project_root = os.path.abspath(os.path.join(current_file_dir, '..'))
    # Construct the path to the 'data' directory
    data_dir = os.path.join(project_root, 'data')
    
    # Create the 'data' directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Save the requests to a JSON file using the json library
    with open(os.path.join(data_dir,f'requests{file_sufices}.json'), 'w') as file:
        json.dump(requests, file, separators=(',', ': '))

    return requests

gen_requests_and_save(file_sufices="0", NUM_OF_NODES=10)