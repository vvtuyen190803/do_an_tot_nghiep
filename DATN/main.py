import argparse
from scenario.track import track

def parse_opt():
    parser = argparse.ArgumentParser()
    # Các tham số cơ bản để main.py hiểu được lệnh của bạn
    parser.add_argument('--scenario', type=str, default='track', help='track or counting')
    parser.add_argument('--yolo-model', type=str, default='weights/yolov8n.pt', help='model.pt path')
    parser.add_argument('--tracking-method', type=str, default='bytetrack', help='bytetrack or botsort')
    parser.add_argument('--source', type=str, default='0', help='video file or 0 for webcam')
    parser.add_argument('--conf', type=float, default=0.25, help='confidence threshold')
    parser.add_argument('--show', action='store_true', help='display results')
    parser.add_argument('--save', action='store_true', help='save results')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or cpu')
    parser.add_argument('--classes', nargs='+', type=int, default=[1, 2, 3, 5, 7], help='filter classes: 1=bicycle, 2=car, 3=motorcycle, 5=bus, 7=truck')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    
    # Các tham số mở rộng (nếu cần cho logic sau này)
    parser.add_argument('--speed-method', type=str, default='transform_3d')
    
    return parser.parse_args()

def main():
    args = parse_opt() 
    
    if args.scenario == 'track':
        # Chuyển đổi args từ Object sang Dictionary để file track.py dễ xử lý
        track(vars(args)) 

if __name__ == "__main__":
    main()