import asyncio
import time
from collections import defaultdict
import aiohttp
import numpy as np

print("=" * 40)
print("Message Queue Stress Test")
print("=" * 40)

async def send_request(session, url):
    start_time = time.time()
    async with session.post(url) as response:
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        return response.status, response_time_ms

async def stress_test(target_url, initial_rps, max_concurrent_tasks=1000):
    semaphore = asyncio.Semaphore(max_concurrent_tasks)
    results = defaultdict(list)
    current_rps = initial_rps
    rps_history = []
    max_actual_rps = 0

    async def limited_request(session, url):
        async with semaphore:
            return await send_request(session, url)

    async with aiohttp.ClientSession() as session:
        while True:
            start_time = time.time()
            tasks = []
            
            print(f"\rTesting {current_rps} RPS... (Max RPS: {max_actual_rps:.2f})", end="", flush=True)
            for _ in range(current_rps):
                tasks.append(asyncio.create_task(limited_request(session, target_url)))
                await asyncio.sleep(1 / current_rps)

            responses = await asyncio.gather(*tasks)
            end_time = time.time()

            for status, response_time in responses:
                results[status].append(response_time)

            actual_duration = end_time - start_time
            actual_rps = len(responses) / actual_duration
            success_rate = len([r for r in responses if r[0] == 200]) / len(responses) if responses else 0

            rps_history.append((current_rps, actual_rps, success_rate))
            max_actual_rps = max(max_actual_rps, actual_rps)

            if success_rate >= 0.99:
                current_rps += 100
            elif success_rate < 0.90:
                break
            else:
                current_rps += 100

            # Stop if the max actual RPS is less than 50% of the current RPS
            if current_rps > 1000 and max_actual_rps < current_rps * 0.5:
                break

            # If we've tested more than 100 different RPS values, stop
            if len(rps_history) > 100:
                break

    max_stable_rps = max([rps for rps, _, sr in rps_history if sr >= 0.99], default=0)
    return max_stable_rps, results, rps_history

def calculate_percentile(data, percentile):
    return np.percentile(data, percentile)

# Parameters for the stress test
TARGET_URL = "http://localhost:80/order/place"
INITIAL_RPS = 100
MAX_CONCURRENT_TASKS = 1024 # Max nginx workers

# Run the stress test
max_rps, results, rps_history = asyncio.run(stress_test(TARGET_URL, INITIAL_RPS, MAX_CONCURRENT_TASKS))

print("\n\nFinal Stress Test Results")
print("-------------------------")
print(f"Target URL: {TARGET_URL}")
print(f"Maximum Stable RPS: {max_rps:.2f}")

print("\nRPS History:")
for rps, actual_rps, success_rate in rps_history:
    print(f"Target RPS: {rps}, Actual RPS: {actual_rps:.2f}, Success Rate: {success_rate:.2%}")

successful_responses = results.get(200, [])
print("\nResponse Time Metrics for Successful Requests (in ms):")
print(f"Total Successful Requests: {len(successful_responses)}")
if successful_responses:
    print(f"Mean: {np.mean(successful_responses):.2f}")
    print(f"Median: {np.median(successful_responses):.2f}")
    print(f"90th Percentile: {calculate_percentile(successful_responses, 90):.2f}")
    print(f"95th Percentile: {calculate_percentile(successful_responses, 95):.2f}")
    print(f"99th Percentile: {calculate_percentile(successful_responses, 99):.2f}")

print("\nResponse Status Code Distribution:")
for status, times in results.items():
    print(f"Status {status}: {len(times)} requests")
