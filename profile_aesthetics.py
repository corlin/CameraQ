import cv2
import numpy as np
import time
from src.core.analyzers.aesthetics_analyzer import AestheticsAnalyzer
from src.core.entities import BoundingBox

def profile_analyzer():
    analyzer = AestheticsAnalyzer()
    
    # Create a dummy image (e.g. 1920x1080)
    frame = np.random.randint(0, 256, (1080, 1920, 3), dtype=np.uint8)
    
    # Dummy bounding box
    primary_box = BoundingBox(x=800, y=400, width=300, height=500)
    
    times = []
    # Warmup
    for _ in range(10):
        analyzer.analyze(frame, primary_box)
        
    for _ in range(100):
        start = time.perf_counter()
        analyzer.analyze(frame, primary_box)
        times.append(time.perf_counter() - start)
        
    avg_time = sum(times) / len(times)
    print(f"Average execution time: {avg_time * 1000:.2f} ms")

if __name__ == '__main__':
    profile_analyzer()
