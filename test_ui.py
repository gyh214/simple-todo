# -*- coding: utf-8 -*-
"""
UI 테스트 스크립트 - 반복 설정 UI 확인
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.presentation.dialogs.edit_dialog import EditDialog
from src.domain.value_objects.recurrence_rule import RecurrenceRule
from datetime import datetime, timedelta

def test_edit_dialog_ui():
    """편집 다이얼로그 UI 테스트"""
    # 로그 파일에 출력
    import io
    import contextlib

    log_file = open("test_ui_log.txt", "w", encoding="utf-8")

    try:
        app = QApplication(sys.argv)

        # 다이얼로그 생성
        dialog = EditDialog()

        # UI 요소 존재 확인
        log_file.write("=== UI 요소 확인 ===\n")
        log_file.write(f"1. 종료일 체크박스 존재: {hasattr(dialog, 'recurrence_end_checkbox')}\n")
        log_file.write(f"2. 종료일 선택 버튼 존재: {hasattr(dialog, 'recurrence_end_btn')}\n")
        log_file.write(f"3. 요일 컨테이너 존재: {hasattr(dialog, 'weekdays_container')}\n")
        log_file.write(f"4. 요일 체크박스 개수: {len(dialog.weekday_checkboxes) if hasattr(dialog, 'weekday_checkboxes') else 0}\n")
        log_file.write(f"5. 하위 할일 복사 체크박스 존재: {hasattr(dialog, 'copy_subtasks_checkbox')}\n")

        # 반복 규칙 설정 테스트
        log_file.write("\n=== 반복 규칙 설정 테스트 ===\n")
        test_recurrence = RecurrenceRule.create(
            frequency="weekly",
            end_date=datetime.now() + timedelta(days=30),
            weekdays=[0, 2, 4],  # 월, 수, 금
            copy_subtasks=True
        )

        # set_todo로 반복 규칙 적용
        dialog.set_todo(
            todo_id="test-id",
            content="테스트 할일",
            due_date=datetime.now().isoformat(),
            recurrence=test_recurrence
        )

        log_file.write(f"5.5. set_todo() 직후 요일 컨테이너 isVisible(): {dialog.weekdays_container.isVisible()}\n")
        log_file.write(f"5.6. set_todo() 직후 요일 컨테이너 isHidden(): {dialog.weekdays_container.isHidden()}\n")

        # 다이얼로그 표시
        dialog.show()

        # Qt 이벤트 큐 처리 (시그널 처리 완료 대기)
        app.processEvents()

        log_file.write(f"5.7. show() + processEvents() 후 요일 컨테이너 isVisible(): {dialog.weekdays_container.isVisible()}\n")
        log_file.write(f"5.8. show() + processEvents() 후 요일 컨테이너 isHidden(): {dialog.weekdays_container.isHidden()}\n")
        log_file.write(f"6. 반복 활성화 체크: {dialog.recurrence_enabled_checkbox.isChecked()}\n")
        log_file.write(f"7. 빈도 선택값: {dialog.recurrence_frequency_combo.currentData()}\n")
        log_file.write(f"8. 종료일 체크: {dialog.recurrence_end_checkbox.isChecked()}\n")
        log_file.write(f"9. 종료일 버튼 텍스트: {dialog.recurrence_end_btn.text()}\n")
        log_file.write(f"10. 요일 컨테이너 표시: {dialog.weekdays_container.isVisible()}\n")

        checked_weekdays = [
            i for i, cb in enumerate(dialog.weekday_checkboxes)
            if cb.isChecked()
        ]
        log_file.write(f"11. 선택된 요일: {checked_weekdays}\n")
        log_file.write(f"12. 하위 할일 복사 체크: {dialog.copy_subtasks_checkbox.isChecked()}\n")

        # get_recurrence 테스트
        log_file.write("\n=== get_recurrence() 테스트 ===\n")
        retrieved_recurrence = dialog.get_recurrence()
        log_file.write(f"13. 반환된 규칙 존재: {retrieved_recurrence is not None}\n")
        if retrieved_recurrence:
            log_file.write(f"14. 빈도: {retrieved_recurrence.frequency}\n")
            log_file.write(f"15. 종료일 존재: {retrieved_recurrence.end_date is not None}\n")
            log_file.write(f"16. 요일: {retrieved_recurrence.weekdays}\n")
            log_file.write(f"17. 하위 할일 복사: {retrieved_recurrence.copy_subtasks}\n")

        log_file.write("\n=== 모든 테스트 완료 ===\n")
        log_file.flush()

        print("테스트 결과가 test_ui_log.txt 파일에 저장되었습니다.")
        print("다이얼로그가 표시됩니다. 수동으로 확인 후 창을 닫으세요.")

        # 다이얼로그 표시 (수동 확인용)
        dialog.show()

        sys.exit(app.exec())
    finally:
        log_file.close()

if __name__ == "__main__":
    test_edit_dialog_ui()
