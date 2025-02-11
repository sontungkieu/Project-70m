import subprocess
from time import perf_counter
import psutil

def run_test_bo_doi_cong_nghiep():
    tin = perf_counter()
    process = subprocess.Popen(['python', 'test_bo_doi_cong_nghiep.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    memory_usage = 0

    while process.poll() is None:
        memory_info = psutil.Process(process.pid).memory_info()
        memory_usage = max(memory_usage, memory_info.rss)  # Get the peak memory usage

    stdout, stderr = process.communicate()
    with open('stdout_output.txt', 'wb') as stdout_file:
        stdout_file.write(stdout)
    with open('stderr_output.txt', 'wb') as stderr_file:
        stderr_file.write(stderr)

    return perf_counter() - tin, memory_usage

if __name__ == "__main__":
    run_time, memory_usage = run_test_bo_doi_cong_nghiep()
    print(f"ORTools run in {run_time:.2f}s")
    print(f"Peak memory usage: {memory_usage / (1024 * 1024):.2f} MB")
    # intel i5-9300H 4 cores - 8 threads, 16GB RAM, 145.44s


"""
import subprocess
from time import perf_counter

def run_test_bo_doi_cong_nghiep():
    tin = perf_counter()
    # Run the test_bo_doi_cong_nghiep.py script and redirect stdout and stderr to separate files
    with open('stdout_output.txt', 'w') as stdout_file, open('stderr_output.txt', 'w') as stderr_file:
        subprocess.run(['python', 'test_bo_doi_cong_nghiep.py'], stdout=stdout_file, stderr=stderr_file)
    return perf_counter() - tin

if __name__ == "__main__":
    run_time = run_test_bo_doi_cong_nghiep()
    print(f"ORTools run in {run_time:.2f}s") 
    # intel i5-9300H 4 cores - 8 threads, 16GB RAM, 145.43666220002342s

"""