"""
Canon 100D 카메라 연결 및 파일 관리 모듈
"""

import os
import subprocess
import time
import gphoto2 as gp
from typing import List, Dict, Optional


def kill_camera_processes():
    """macOS 카메라 프로세스 강제 종료"""
    subprocess.run(['pkill', '-9', '-f', 'ptpcamerad'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-9', '-f', 'mscamerad'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-9', '-f', 'icdd'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-9', '-f', 'cameracaptured'], stderr=subprocess.DEVNULL)


class CameraConnection:
    """Canon 카메라 연결 및 파일 관리 클래스"""

    TARGET_CAMERA = "Canon EOS 100D"  # 연결할 카메라 모델명

    def __init__(self):
        self.camera = None
        self.is_connected = False
        self.camera_name = "Unknown"

    def _find_canon_camera(self):
        """Canon EOS 100D 카메라를 찾아서 포트 반환"""
        try:
            cameras = gp.Camera.autodetect()
            for name, port in cameras:
                if self.TARGET_CAMERA in name or "Canon" in name:
                    return name, port
        except:
            pass
        return None, None

    def connect(self) -> bool:
        """카메라 연결 (Canon EOS 100D 명시적 지정, 3회 재시도)"""
        MAX_ATTEMPTS = 3

        for attempt in range(MAX_ATTEMPTS):
            # 프로세스 종료 후 즉시 연결 시도 (딜레이 최소화)
            kill_camera_processes()
            time.sleep(0.1)  # 최소 딜레이

            try:
                # Canon 카메라 찾기
                camera_name, port = self._find_canon_camera()

                if port:
                    # 특정 포트로 연결
                    self.camera = gp.Camera()
                    port_info_list = gp.PortInfoList()
                    port_info_list.load()
                    idx = port_info_list.lookup_path(port)
                    self.camera.set_port_info(port_info_list[idx])
                    self.camera.init()
                else:
                    # 기본 연결 시도
                    self.camera = gp.Camera()
                    self.camera.init()

                self.is_connected = True
                abilities = self.camera.get_abilities()
                self.camera_name = abilities.model

                # Canon 카메라인지 확인
                if "Canon" in self.camera_name:
                    print(f"✅ 카메라 연결됨: {self.camera_name}")
                    return True
                else:
                    # Canon이 아니면 연결 해제하고 재시도
                    self.camera.exit()
                    self.is_connected = False
                    continue

            except gp.GPhoto2Error as e:
                self.is_connected = False
                if attempt < MAX_ATTEMPTS - 1:
                    time.sleep(0.2)  # 재시도 전 짧은 대기
                    continue
                print(f"❌ 카메라 연결 실패: {e}")
                return False

        print(f"❌ 카메라 연결 실패: {MAX_ATTEMPTS}회 시도 모두 실패")
        return False

    def disconnect(self):
        """카메라 연결 해제"""
        if self.camera and self.is_connected:
            self.camera.exit()
            self.is_connected = False
            print("📴 카메라 연결 해제됨")

    def get_all_files(self) -> List[Dict[str, any]]:
        """카메라 내 모든 JPG 파일 목록 조회"""
        if not self.is_connected:
            print("⚠️ 카메라가 연결되지 않았습니다.")
            return []

        files_list = []

        def scan_folder(path: str):
            """재귀적으로 폴더 스캔"""
            try:
                # 폴더 목록 가져오기
                folder_list = self.camera.folder_list_folders(path)
                folders = [folder_list.get_name(i) for i in range(folder_list.count())]

                # 파일 목록 가져오기
                file_list = self.camera.folder_list_files(path)
                files = [file_list.get_name(i) for i in range(file_list.count())]

                # JPG 파일 수집
                for filename in files:
                    if filename.lower().endswith(('.jpg', '.jpeg')):
                        file_info = self.camera.file_get_info(path, filename)
                        size_mb = file_info.file.size / (1024 * 1024)
                        files_list.append({
                            'path': path,
                            'name': filename,
                            'size': size_mb,
                            'full_path': f"{path}/{filename}"
                        })

                # 하위 폴더 재귀 탐색
                for folder_name in folders:
                    subpath = path.rstrip('/') + '/' + folder_name
                    scan_folder(subpath)

            except gp.GPhoto2Error:
                pass

        # 루트부터 전체 탐색
        scan_folder("/")
        return files_list

    def download_file(self, file_info: Dict[str, any], output_folder: str) -> bool:
        """특정 파일 다운로드"""
        if not self.is_connected:
            print("⚠️ 카메라가 연결되지 않았습니다.")
            return False

        try:
            # 출력 폴더 생성
            os.makedirs(output_folder, exist_ok=True)

            # 파일 다운로드
            camera_file = self.camera.file_get(
                file_info['path'],
                file_info['name'],
                gp.GP_FILE_TYPE_NORMAL
            )

            # 저장 경로
            target_path = os.path.join(output_folder, file_info['name'])

            # 파일 저장
            camera_file.save(target_path)
            return True

        except gp.GPhoto2Error as e:
            print(f"❌ 다운로드 실패 ({file_info['name']}): {e}")
            return False

    def download_new_files(self, output_folder: str, processed_files: set) -> List[str]:
        """새로운 파일만 다운로드"""
        all_files = self.get_all_files()
        new_files = []

        for file_info in all_files:
            # 이미 처리된 파일은 건너뛰기
            if file_info['full_path'] in processed_files:
                continue

            # 파일 다운로드
            if self.download_file(file_info, output_folder):
                new_files.append(file_info['name'])
                print(f"  ✅ {file_info['name']} 다운로드 완료")

        return new_files

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.disconnect()
