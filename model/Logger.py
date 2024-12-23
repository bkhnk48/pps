import os
import csv

class Logger:
    def __init__(self):
        self.index = 0
        pass
    def count_csv_rows(self, fileName):
        with open(fileName, mode='r', newline='') as file:
            reader = csv.reader(file)
            row_count = sum(1 for row in reader)
        return row_count
    
    def get_max_value(self, fileName, columnName):
        try:
            with open(fileName, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                max_value = None
                
                for row in reader:
                    if columnName in row and row[columnName]:
                        value = float(row[columnName])
                        if max_value is None or value > max_value:
                            max_value = value
                return max_value if max_value is not None else 0
        except FileNotFoundError:
            #print(f"File {fileName} không tồn tại.")
            return 0
        except ValueError:
            return 0

# Ví dụ sử dụng
#fileName = 'data.csv'
#columnName = 'name'
#print(f'Giá trị lớn nhất trong cột {columnName}: {get_max_value(fileName, columnName)}')


    def log(self, fileName, map, totalAGVs, H, d, solution, reachingTarget, halting, objectiveValue, runTime, solving, pedestrians_mode, formatted_now):
        # Kiểm tra xem fileName có đuôi .csv chưa, nếu chưa thì thêm vào
        if not fileName.endswith('.csv'):
            fileName += '.csv'

        # Kiểm tra xem file đã tồn tại chưa
        file_exists = os.path.isfile(fileName)

        # Mở file ở chế độ append
        with open(fileName, mode='a', newline='') as file:
            writer = csv.writer(file)

            # Nếu file chưa tồn tại, thêm dòng tiêu đề
            if not file_exists:
                writer.writerow(['No', 'Map', 'Total AGVs', 'Horizontal Time', 'Time step', 'Solution', 
                                 'Num of Reaching Target AGVs', 'Num of Halting AGVs', 
                                 'Objective Value', 'Running Time(s)', '# Of Solving', 'Pedestrian simulation mode', 'At'])
                
            initialIndex = self.get_max_value(fileName, 'No') + 1

            # Thêm dòng dữ liệu mới
            writer.writerow([initialIndex, map, totalAGVs, H, d, solution, reachingTarget, halting, 
                             objectiveValue, runTime, solving, pedestrians_mode, formatted_now])

# Ví dụ sử dụng
#logger = Logger()
#logger.log('logfile', 'Map1', 10, 5, 'Solution1', 8, 2, 100.0, 12.5)
