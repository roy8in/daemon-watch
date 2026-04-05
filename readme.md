# Project Specification: macOS Menu Bar Process Monitor (Daemon Watch)

## 1. Overview
macOS의 메뉴 바(상태 표시줄)에 상주하며, 시스템의 백그라운드 작업(Cron)과 Node.js 프로세스(PM2)의 상태를 실시간으로 모니터링하고 제어할 수 있는 경량 유틸리티 애플리케이션.

## 2. Technology Stack
* **Language:** Python 3.x
* **GUI Framework:** `rumps` (macOS Menu Bar App 구축)
* **System Interaction:** `subprocess` (셸 명령어 실행 및 결과 파싱)
* **Text Processing:** `cron-descriptor` (Cron 표현식을 영어 텍스트로 변환), `re` (정규표현식 파싱)

## 3. Core Features

### 3.1. General Settings & UI
* **UI Language:** 모든 메뉴, 레이블, 상태 메시지는 영어(English)로 표기.
* **Polling Interval:** 사용자가 백그라운드 데이터 수집 주기 설정 가능 (기본값: 60초).
* **Manual Refresh:** 메뉴 바 클릭 시 즉시 최신 상태로 동기화.

### 3.2. Cron Management
* **List Jobs:** `crontab -l` 결과를 파싱하여 등록된 스케줄 목록 표시.
* **Human-Readable Format:** `0 2 * * *` 형태의 표현식을 "At 02:00 AM"과 같은 직관적인 영어 문장으로 변환.
* **Custom Labeling (User-Defined):** * UI 내 'Edit Label' 메뉴를 통해 사용자가 직접 작업 이름을 지정 및 수정 가능.
    * 앱은 해당 라인 상단에 `# NAME: [Label]` 주석을 삽입하여 데이터를 영구 보존.
* **Toggle (Enable/Disable):** 메뉴 클릭을 통해 crontab 라인 앞에 주석(`#`)을 추가/제거하여 스케줄 활성화/비활성화.
* **Edit Schedule:** UI 팝업을 통해 기존 스케줄의 주기(시간 설정)를 새로운 값으로 수정.
* **Run Now:** 지정된 시간이 아니더라도 해당 스크립트를 즉시 1회 백그라운드 실행.
* **View Logs:** 해당 작업의 출력(stdout/stderr) 로그 파일의 최근 10줄을 확인.

### 3.3. PM2 Management
* **List Processes:** `pm2 jlist`를 통해 프로세스 목록 및 리소스 사용량(CPU, Memory) 표시.
* **Status Indicator:** Online / Stopped / Errored 상태에 따른 시각적 구분.
* **Process Control:**
    * `Start`: 중지된 프로세스 실행.
    * `Restart`: 실행 중인 프로세스를 종료 후 즉시 재시작.
    * `Stop`: 실행 중인 프로세스 정지.
* **View Logs:** `pm2 logs [id] --lines 10 --nostream` 명령을 호출하여 최근 로그 확인.

## 4. Architecture & Data Flow

1.  **Data Fetcher Module:** 설정된 주기에 따라 백그라운드에서 `crontab` 및 `pm2` 시스템 명령 실행.
2.  **Parser Module:** 수집된 텍스트/JSON 데이터를 구조화. 주석 기반 Label 파싱 및 시간 표현식 번역 수행.
3.  **UI Controller Module:** 파싱된 데이터를 바탕으로 `rumps` 메뉴 아이템을 동적으로 생성 및 상태 갱신.
4.  **Action Handler Module:** 사용자의 제어 명령(Start, Stop, Label Edit 등)을 수신하여 실제 시스템 파일(crontab)을 수정하거나 CLI 명령을 실행한 뒤 즉시 UI 새로고침 트리거.