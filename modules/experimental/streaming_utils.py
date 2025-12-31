import numpy as np
import torch

class CircularAudioBuffer:
    """실시간 스트리밍을 위한 순환 버퍼 구조"""
    def __init__(self, capacity_sec=2.0, sample_rate=16000):
        self.capacity = int(capacity_sec * sample_rate)
        self.buffer = np.zeros(self.capacity, dtype=np.float32)
        self.head = 0
        self.size = 0

    def push(self, data):
        """데이터 삽입 (FIFO)"""
        n = len(data)
        if n > self.capacity:
            data = data[-self.capacity:]
            n = self.capacity
        
        end = (self.head + n) % self.capacity
        if self.head + n <= self.capacity:
            self.buffer[self.head:self.head+n] = data
        else:
            first_part = self.capacity - self.head
            self.buffer[self.head:] = data[:first_part]
            self.buffer[:end] = data[first_part:]
        
        self.head = end
        self.size = min(self.capacity, self.size + n)

class OverlapAddProcessor:
    """프레임 간 불연속성 제거를 위한 Overlap-Add 알고리즘"""
    def __init__(self, frame_size=1024, overlap=256):
        self.frame_size = frame_size
        self.overlap = overlap
        self.window = np.hanning(frame_size)
        self.output_buffer = np.zeros(frame_size * 2)

    def process_frame(self, new_frame):
        """윈도우 함수 적용 및 중첩 가산"""
        applied = new_frame * self.window
        # 이전 프레임의 중첩 구간과 가산
        self.output_buffer[:self.overlap] += applied[:self.overlap]
        # 결과 추출 및 버퍼 시프트
        result = self.output_buffer[:self.frame_size - self.overlap]
        self.output_buffer = np.roll(self.output_buffer, -(self.frame_size - self.overlap))
        self.output_buffer[-(self.frame_size - self.overlap):] = 0
        self.output_buffer[:self.frame_size] += applied
        return result

if __name__ == "__main__":
    print("Streaming Utils (CircularBuffer, OverlapAdd) initialized.")
