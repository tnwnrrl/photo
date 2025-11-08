#!/usr/bin/env python3
"""
Canon 100D 사진 자동 처리 GUI 프로그램

기능:
- 모니터링 시작/종료 버튼
- 실시간 로그 출력
- 처리 통계 표시
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
import queue
import sys
import os
import json
import subprocess
from datetime import datetime
from utils.camera import CameraConnection
from utils.image_processor import ImageProcessor


def kill_camera_processes():
    """카메라를 점유하고 있는 프로세스 종료"""
    try:
        subprocess.run(['killall', 'Image Capture'], stderr=subprocess.DEVNULL)
        subprocess.run(['killall', 'ptpcamerad'], stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


class PhotoProcessorGUI:
    """GUI 메인 클래스"""

    def __init__(self, root):
        self.root = root
        self.root.title("Canon 100D 사진 자동 처리")
        self.root.geometry("800x700")

        # 상태 변수
        self.is_monitoring = False
        self.monitor_thread = None
        self.log_queue = queue.Queue()

        # 통계
        self.stats = {
            'downloaded': 0,
            'processed': 0,
            'errors': 0
        }

        # 설정 로드
        self.load_config()

        # UI 생성
        self.create_widgets()

        # 로그 큐 체크
        self.check_log_queue()

    def load_config(self):
        """설정 파일 로드"""
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.original_folder = self.config['paths']['original_folder']
        self.overlay_image = self.config['paths']['overlay_image']
        self.output_folder = self.config['paths']['output_folder']
        self.check_interval = self.config['camera']['check_interval_seconds']
        self.processed_files_db = self.config['monitoring']['processed_files_db']

    def save_config(self):
        """설정 파일 저장"""
        self.config['paths']['original_folder'] = self.original_folder
        self.config['paths']['overlay_image'] = self.overlay_image
        self.config['paths']['output_folder'] = self.output_folder

        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def create_widgets(self):
        """UI 위젯 생성"""
        # 상단 프레임 - 제목
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)

        title_label = ttk.Label(
            title_frame,
            text="Canon 100D 사진 자동 처리",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack()

        # 설정 프레임
        settings_frame = ttk.LabelFrame(self.root, text="설정", padding="10")
        settings_frame.pack(fill=tk.X, padx=10, pady=5)

        # 다운로드 폴더
        download_frame = ttk.Frame(settings_frame)
        download_frame.pack(fill=tk.X, pady=2)

        ttk.Label(download_frame, text="다운로드 폴더:", width=15).pack(side=tk.LEFT)
        self.download_folder_var = tk.StringVar(value=self.original_folder)
        download_entry = ttk.Entry(download_frame, textvariable=self.download_folder_var, width=40)
        download_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(download_frame, text="찾아보기",
                   command=lambda: self.browse_folder(self.download_folder_var, 'original_folder')).pack(side=tk.LEFT)

        # 출력 폴더
        output_frame = ttk.Frame(settings_frame)
        output_frame.pack(fill=tk.X, pady=2)

        ttk.Label(output_frame, text="출력 폴더:", width=15).pack(side=tk.LEFT)
        self.output_folder_var = tk.StringVar(value=self.output_folder)
        output_entry = ttk.Entry(output_frame, textvariable=self.output_folder_var, width=40)
        output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="찾아보기",
                   command=lambda: self.browse_folder(self.output_folder_var, 'output_folder')).pack(side=tk.LEFT)

        # 오버레이 이미지
        overlay_frame = ttk.Frame(settings_frame)
        overlay_frame.pack(fill=tk.X, pady=2)

        ttk.Label(overlay_frame, text="오버레이 이미지:", width=15).pack(side=tk.LEFT)
        self.overlay_image_var = tk.StringVar(value=self.overlay_image)
        overlay_entry = ttk.Entry(overlay_frame, textvariable=self.overlay_image_var, width=40)
        overlay_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(overlay_frame, text="찾아보기",
                   command=self.browse_overlay_file).pack(side=tk.LEFT)

        # 상태 프레임
        status_frame = ttk.LabelFrame(self.root, text="상태", padding="10")
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = ttk.Label(
            status_frame,
            text="⚪ 대기 중",
            font=("Helvetica", 12)
        )
        self.status_label.pack()

        # 통계 프레임
        stats_frame = ttk.LabelFrame(self.root, text="처리 통계", padding="10")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack()

        ttk.Label(stats_grid, text="다운로드:").grid(row=0, column=0, padx=5)
        self.downloaded_label = ttk.Label(stats_grid, text="0", font=("Helvetica", 12, "bold"))
        self.downloaded_label.grid(row=0, column=1, padx=5)

        ttk.Label(stats_grid, text="합성 완료:").grid(row=0, column=2, padx=5)
        self.processed_label = ttk.Label(stats_grid, text="0", font=("Helvetica", 12, "bold"))
        self.processed_label.grid(row=0, column=3, padx=5)

        ttk.Label(stats_grid, text="오류:").grid(row=0, column=4, padx=5)
        self.errors_label = ttk.Label(stats_grid, text="0", font=("Helvetica", 12, "bold"))
        self.errors_label.grid(row=0, column=5, padx=5)

        # 컨트롤 프레임
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X, padx=10)

        self.start_button = ttk.Button(
            control_frame,
            text="▶ 모니터링 시작",
            command=self.start_monitoring,
            state=tk.NORMAL
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            control_frame,
            text="⏹ 모니터링 종료",
            command=self.stop_monitoring,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.reconnect_button = ttk.Button(
            control_frame,
            text="🔄 카메라 재연결",
            command=self.reconnect_camera
        )
        self.reconnect_button.pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text=f"감지 간격: {self.check_interval}초").pack(side=tk.LEFT, padx=20)

        # 로그 프레임
        log_frame = ttk.LabelFrame(self.root, text="실시간 로그", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            wrap=tk.WORD,
            font=("Courier", 10)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 하단 프레임
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)

        ttk.Button(
            bottom_frame,
            text="로그 지우기",
            command=self.clear_log
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            bottom_frame,
            text="종료",
            command=self.quit_app
        ).pack(side=tk.RIGHT, padx=5)

    def log(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}\n")

    def check_log_queue(self):
        """로그 큐에서 메시지 가져와 표시"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass

        # 100ms마다 체크
        self.root.after(100, self.check_log_queue)

    def update_stats(self):
        """통계 업데이트"""
        self.downloaded_label.config(text=str(self.stats['downloaded']))
        self.processed_label.config(text=str(self.stats['processed']))
        self.errors_label.config(text=str(self.stats['errors']))

    def clear_log(self):
        """로그 지우기"""
        self.log_text.delete(1.0, tk.END)

    def start_monitoring(self):
        """모니터링 시작"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="🟢 모니터링 중")

        self.log("=" * 50)
        self.log("모니터링 시작")
        self.log("=" * 50)

        # 백그라운드 스레드 시작
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """모니터링 종료"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="⚪ 대기 중")

        self.log("=" * 50)
        self.log("모니터링 종료")
        self.log("=" * 50)

    def monitoring_loop(self):
        """모니터링 루프 (백그라운드)"""
        import time

        # 처리된 파일 목록 로드
        processed_files = self.load_processed_files()

        # 이미지 프로세서 초기화
        image_processor = ImageProcessor(self.overlay_image)

        while self.is_monitoring:
            try:
                self.log("카메라 확인 중...")

                with CameraConnection() as camera:
                    if not camera.is_connected:
                        self.log("❌ 카메라 연결 실패")
                        time.sleep(self.check_interval)
                        continue

                    # 새 파일 다운로드
                    all_files = camera.get_all_files()
                    new_files = []

                    for file_info in all_files:
                        if file_info['full_path'] in processed_files:
                            continue

                        if camera.download_file(file_info, self.original_folder):
                            new_files.append(file_info['name'])
                            processed_files.add(file_info['full_path'])
                            self.stats['downloaded'] += 1
                            self.log(f"  ✅ {file_info['name']} 다운로드 완료")

                    if new_files:
                        self.log(f"✅ 새 파일 {len(new_files)}개 발견!")

                        # PNG 합성 처리
                        for filename in new_files:
                            input_path = os.path.join(self.original_folder, filename)
                            output_path = os.path.join(self.output_folder, filename)

                            if image_processor.composite_image(input_path, output_path):
                                self.stats['processed'] += 1
                                self.log(f"  🖼️ {filename} 합성 완료")
                            else:
                                self.stats['errors'] += 1
                                self.log(f"  ❌ {filename} 합성 실패")

                        # 통계 업데이트
                        self.root.after(0, self.update_stats)

                        # 처리된 파일 목록 저장
                        self.save_processed_files(processed_files)
                    else:
                        self.log("  ✓ 새 파일 없음")

            except Exception as e:
                self.log(f"❌ 오류: {e}")
                self.stats['errors'] += 1
                self.root.after(0, self.update_stats)

            # 대기
            time.sleep(self.check_interval)

    def load_processed_files(self):
        """처리된 파일 목록 로드"""
        if os.path.exists(self.processed_files_db):
            with open(self.processed_files_db, 'r') as f:
                return set(json.load(f))
        return set()

    def save_processed_files(self, processed_files):
        """처리된 파일 목록 저장"""
        with open(self.processed_files_db, 'w') as f:
            json.dump(list(processed_files), f, indent=2)

    def browse_folder(self, var, config_key):
        """폴더 선택 다이얼로그"""
        current_path = var.get()
        folder_path = filedialog.askdirectory(
            title="폴더 선택",
            initialdir=current_path if os.path.exists(current_path) else "."
        )

        if folder_path:
            var.set(folder_path)
            # 설정 업데이트
            if config_key == 'original_folder':
                self.original_folder = folder_path
            elif config_key == 'output_folder':
                self.output_folder = folder_path

            self.save_config()
            self.log(f"✅ {config_key} 경로 변경: {folder_path}")

    def browse_overlay_file(self):
        """오버레이 파일 선택 다이얼로그"""
        current_path = self.overlay_image_var.get()
        file_path = filedialog.askopenfilename(
            title="PNG 파일 선택",
            initialdir=os.path.dirname(current_path) if os.path.exists(current_path) else ".",
            filetypes=[("PNG 파일", "*.png"), ("모든 파일", "*.*")]
        )

        if file_path:
            self.overlay_image_var.set(file_path)
            self.overlay_image = file_path
            self.save_config()
            self.log(f"✅ 오버레이 이미지 변경: {file_path}")

    def reconnect_camera(self):
        """카메라 재연결 시도"""
        self.log("🔄 카메라 재연결 시도 중...")

        # 1. 카메라 점유 프로세스 종료
        kill_camera_processes()
        self.log("  ✓ 카메라 점유 프로세스 종료")

        # 2. 잠시 대기
        import time
        time.sleep(2)

        # 3. 카메라 연결 테스트
        try:
            with CameraConnection() as camera:
                if camera.is_connected:
                    self.log(f"✅ 카메라 재연결 성공: {camera.camera_name}")
                else:
                    self.log("❌ 카메라 재연결 실패")
        except Exception as e:
            self.log(f"❌ 카메라 재연결 오류: {e}")

    def quit_app(self):
        """프로그램 종료"""
        if self.is_monitoring:
            self.stop_monitoring()

        # 카메라 점유 프로세스 종료
        self.log("🧹 카메라 프로세스 정리 중...")
        kill_camera_processes()
        self.log("✅ 프로그램 종료")

        self.root.quit()


def main():
    """메인 실행 함수"""
    # 설정 파일 확인
    if not os.path.exists("config.json"):
        print("❌ config.json 파일을 찾을 수 없습니다.")
        sys.exit(1)

    # 카메라 점유 프로세스 자동 종료
    print("🔄 카메라 점유 프로세스 확인 중...")
    kill_camera_processes()
    print("✅ 카메라 점유 프로세스 종료 완료")

    # GUI 실행
    root = tk.Tk()
    app = PhotoProcessorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()


if __name__ == "__main__":
    main()
