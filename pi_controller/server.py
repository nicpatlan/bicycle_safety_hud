from enum import Enum
import queue
import sys
import threading
import atexit
import time
import asyncio
from bleak import BleakClient

testing = len(sys.argv) >= 2 and sys.argv[1] == "test"
sys.path.insert(1, '/cv')
if testing:
    from cv.testing_vision import get_obj_sizes, getImgArea
    def getSpeed() -> float:
        return 10
else:
    from cv.pi_vision import get_obj_sizes, getImgArea
    from speedometer.speedometer import getSpeed

FRAMES_CAN_SKIP = 2
IMG_AREA = getImgArea()
PCT_OF_IMG_AREA = 0.6 if testing else 0.4

class CarStatus(Enum):
    CAR_BEHIND = "CAR_BEHIND"
    CAR_APPROACHING = "CAR_APPROACHING"
    NO_CAR = "NO_CAR"

def get_car_status(previous_max_size: int, skipped_frames: int, car_status: CarStatus = CarStatus.NO_CAR):
    obj_sizes = get_obj_sizes()

    max_size = max(obj_sizes, default=0)

    if max_size > 0:
        if max_size >= IMG_AREA * PCT_OF_IMG_AREA:
            car_status = CarStatus.CAR_BEHIND
        elif max_size > previous_max_size * 1.1:
            car_status = CarStatus.CAR_APPROACHING
        else:
            car_status = CarStatus.CAR_BEHIND
        previous_max_size = max_size
    else:
        if skipped_frames < FRAMES_CAN_SKIP and previous_max_size > 0:
            skipped_frames += 1
        else:
            skipped_frames = 0
            previous_max_size = 0
            car_status = CarStatus.NO_CAR

    return car_status, previous_max_size, skipped_frames

def car_inference_thread(carq: queue.Queue, stop_event: threading.Event):
    previous_max_size = 0
    skipped_frames = 0
    status = CarStatus.NO_CAR
    while True:
        status, previous_max_size, skipped_frames = get_car_status(previous_max_size, skipped_frames, status)
        carq.put(status)
        if stop_event.is_set():
            return

carq = queue.Queue(3)
bleakq = queue.Queue(2)
stop_event = threading.Event()

car_th = threading.Thread(target=car_inference_thread, name='car_inference_thread', args=(carq, stop_event))
car_th.daemon = True
car_th.start()

main_thread_car_status = "NO_CAR"
main_thread_bike_speed = "0"

address = "84:fc:e6:84:2e:fe"    # MAC address of esp32
SERVICE_UUID_CHAR1 = "fcde0001-e5b0-4f32-ad25-d70e07e9eeea"   # car_status
SERVICE_UUID_CHAR2 = "fcde0002-e5b0-4f32-ad25-d70e07e9eeea"   # bike speed

async def bleak_thread_fn(bleakq: queue.Queue, stop_event: threading.Event, mac_addr: str) -> None:
    while True:
        try:
            async with BleakClient(mac_addr) as client:
                while True:
                    if not bleakq.qsize() == 0:
                        car_status, bike_speed = bleakq.get()
                        await client.write_gatt_char(SERVICE_UUID_CHAR1, bytearray(car_status, encoding='utf-8'), True)
                        await client.write_gatt_char(SERVICE_UUID_CHAR2, bytearray(bike_speed, encoding='utf-8'), True)
                        print(f"Car Status: {car_status}, Bike Speed: {bike_speed}")
                    if stop_event.is_set():
                        return
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

def between_callback(bleakq: queue.Queue, stop_event: threading.Event, mac_addr: str):
    asyncio.run(bleak_thread_fn(bleakq, stop_event, mac_addr))

            
bleak_th = threading.Thread(target=between_callback, name='bleak_thread_fn', args=(bleakq, stop_event, address))
bleak_th.daemon = True
bleak_th.start()

def cleanup():
    stop_event.set()
    car_th.join()
    bleak_th.join()

atexit.register(cleanup)

while True:
    speed = getSpeed()
    if speed is not None:
        main_thread_bike_speed = str(speed)
    if not carq.qsize() == 0:
        main_thread_car_status = str(carq.get())
    # print(f"Speed: {main_thread_bike_speed}, Car Status: {main_thread_car_status}")

    try:
        bleakq.put((main_thread_car_status, main_thread_bike_speed), block=False)
    except:
        print("bleakq full")

    time.sleep(0.05)
