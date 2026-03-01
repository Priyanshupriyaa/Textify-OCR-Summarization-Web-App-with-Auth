# Simplification TODO

## Task 1: Remove unnecessary auth complexity (keep JWT only) ✅
- [x] Remove flask_login imports and LoginManager
- [x] Remove UserMixin
- [x] Remove session-based auth in routes
- [x] Keep JWT only for authentication
- [x] Remove session imports and usage

## Task 2: Remove async/poll architecture (keep sync endpoints) ✅
- [x] Remove `process_ocr_task` function
- [x] Remove `process_summarize_task` function
- [x] Remove `create_task` function
- [x] Remove `update_task_status` function
- [x] Remove `/ocr_async` route
- [x] Remove `/summarize_async` route
- [x] Remove `/task_status` route
- [x] Remove threading imports and usage
- [x] Remove MongoDB tasks collection usage

## Task 3: Simplify OCR to single PSM mode ✅
- [x] Remove OCR mode selector from frontend
- [x] Remove ocr_mode parameter from API
- [x] Use default PSM 6 only
