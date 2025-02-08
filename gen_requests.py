import random
import csv


random.seed(42)

def gen_request(single_start = True, small_weihgt = True):
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
    #số điểm lấy hàng tuỳ ý 
    start_place = random.sample([0, 1, 2, 3], k=random.randint(1, 1 if single_start else 4))
    #chỉ 1 điểm giao hàng cho mỗi đơn
    end_place = random.sample(list(range(4,54)), k=1)
    weight = random.randint(0*100, 3*100)/100 if small_weihgt==True else random.randint(12*100, 30*100)/100 if small_weihgt==False else random.randint(7*100, 20*100)/100
    gen_day = random.randint(0, 3)
    gen_timeframe = sorted(random.sample(list(range(0,24)), k=2))
    return [start_place,end_place,weight,gen_day,gen_timeframe]


def gen_requests_and_save(num_requests = 10, file_sufices = "",seed=42):
    """
    Tạo một số lượng yêu cầu giao hàng ngẫu nhiên và lưu vào tệp CSV.

    Parameters:
    -----------
    num_requests : int, optional (default=10)
        - Số lượng yêu cầu giao hàng cần tạo.

    file_suffix : str, optional (default="")
        - Hậu tố được thêm vào tên tệp CSV. 
        - Nếu không cung cấp, tệp sẽ có tên mặc định là "requests.csv".
        - Nếu cung cấp, tệp sẽ có dạng "requests<file_suffix>.csv".

    Returns:
    --------
    requests: list
        - Danh sách các yêu cầu giao hàng được tạo, mỗi yêu cầu có định dạng giống như kết quả của `gen_request()`.

    Notes:
    ------
    - Hàm này sẽ tạo một tệp CSV có tên "requests<file_suffix>.csv".
    - Nếu tệp đã tồn tại, nội dung sẽ bị ghi đè.
    - Mỗi hàng trong tệp CSV sẽ có định dạng:
      Start Place, End Place, Weight, Gen Day, Gen Timeframe

    Example:
    --------
    >>> requests = gen_requests_and_save(num_requests=5, file_suffix="_test")
    >>> print(requests)
    [[[0], [8], 2.1, 1, [3, 15]], ..., [[2], [27], 1.8, 3, [6, 19]]]

    - File CSV được tạo sẽ có tên "requests_test.csv".
    """
    random.seed(seed)
    requests = [gen_request() for i in range(10)]
    with open(f'requests{file_sufices}.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Start Place', 'End Place', 'Weight', 'Gen Day', 'Gen Timeframe'])
        for request in requests:
            writer.writerow(request)
    return requests


gen_requests_and_save(file_sufices="0")