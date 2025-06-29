import uuid
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import concurrent.futures
import traceback

# Import scanning functions
from lay_data_stock import (
    market_scan_top_picks,
    market_scan_by_category,
    market_scan_parallel
)
from config import GTIConfig

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

@dataclass
class Task:
    task_id: str
    task_type: str
    parameters: Dict[str, Any]
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress_message: str = "Đang khởi tạo tác vụ..."

class TaskManager:
    """
    🚀 Task Manager cho Asynchronous Market Scanning
    
    Quản lý các tác vụ quét thị trường chạy ngầm để tránh timeout
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        self.lock = threading.Lock()
        
        # Auto cleanup expired tasks every 30 minutes
        self.cleanup_timer = threading.Timer(1800, self._cleanup_expired_tasks)
        self.cleanup_timer.daemon = True
        self.cleanup_timer.start()
    
    def create_task(self, task_type: str, parameters: Dict[str, Any]) -> str:
        """
        Tạo một task mới và bắt đầu thực thi ngầm
        
        Args:
            task_type: Loại task (top_picks, sector_scan, category_scan, custom_scan)
            parameters: Tham số cho task
            
        Returns:
            task_id: ID duy nhất của task
        """
        task_id = str(uuid.uuid4())
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            parameters=parameters,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        with self.lock:
            self.tasks[task_id] = task
        
        # Submit task to background executor
        future = self.executor.submit(self._execute_task, task_id)
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Kiểm tra trạng thái của task
        
        Args:
            task_id: ID của task
            
        Returns:
            Dict chứa thông tin trạng thái hoặc None nếu không tìm thấy
        """
        with self.lock:
            task = self.tasks.get(task_id)
            
        if not task:
            return None
            
        # Check if task is expired (older than 1 hour)
        if datetime.now() - task.created_at > timedelta(hours=1):
            task.status = TaskStatus.EXPIRED
            
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "progress_message": task.progress_message,
            "error": task.error,
            "has_result": task.result is not None
        }
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy kết quả của task đã hoàn thành
        
        Args:
            task_id: ID của task
            
        Returns:
            Dict chứa kết quả hoặc None nếu chưa hoàn thành/không tìm thấy
        """
        with self.lock:
            task = self.tasks.get(task_id)
            
        if not task or task.status != TaskStatus.COMPLETED:
            return None
            
        return task.result
    
    def _execute_task(self, task_id: str):
        """
        Thực thi task trong background thread
        """
        with self.lock:
            task = self.tasks.get(task_id)
            
        if not task:
            return
            
        try:
            # Update status to running
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            task.progress_message = "Đang thực hiện phân tích..."
            
            # Execute based on task type
            if task.task_type == "top_picks":
                result = self._execute_top_picks(task)
            elif task.task_type == "sector_scan":
                result = self._execute_sector_scan(task)
            elif task.task_type == "category_scan":
                result = self._execute_category_scan(task)
            elif task.task_type == "custom_scan":
                result = self._execute_custom_scan(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            # Update task with result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.progress_message = "Hoàn thành phân tích!"
            
        except Exception as e:
            # Handle errors
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)
            task.progress_message = f"Lỗi: {str(e)}"
            
            # Log the full traceback for debugging
            print(f"Task {task_id} failed with error: {e}")
            print(traceback.format_exc())
    
    def _execute_top_picks(self, task: Task) -> Dict[str, Any]:
        """Thực thi top picks scan"""
        task.progress_message = "Đang quét toàn thị trường tìm top picks..."
        
        limit = task.parameters.get("limit", 15)
        result = market_scan_top_picks(limit=limit)
        
        return {
            "task_type": "top_picks",
            "parameters": task.parameters,
            "scan_result": result,
            "execution_time": (task.completed_at - task.started_at).total_seconds() if task.completed_at and task.started_at else None
        }
    
    def _execute_sector_scan(self, task: Task) -> Dict[str, Any]:
        """Thực thi sector scan"""
        sector = task.parameters.get("sector")
        task.progress_message = f"Đang quét ngành {sector}..."
        
        min_gti_score = task.parameters.get("min_gti_score", 2)
        min_combined_score = task.parameters.get("min_combined_score", 3)
        
        result = market_scan_by_category(
            category=sector,
            min_gti_score=min_gti_score,
            min_combined_score=min_combined_score
        )
        
        return {
            "task_type": "sector_scan", 
            "parameters": task.parameters,
            "scan_result": result,
            "execution_time": (task.completed_at - task.started_at).total_seconds() if task.completed_at and task.started_at else None
        }
    
    def _execute_category_scan(self, task: Task) -> Dict[str, Any]:
        """Thực thi category scan (vn30, popular, etc.)"""
        category = task.parameters.get("category", "vn30")
        task.progress_message = f"Đang quét danh mục {category}..."
        
        min_gti_score = task.parameters.get("min_gti_score", 2)
        min_combined_score = task.parameters.get("min_combined_score", 3)
        
        result = market_scan_by_category(
            category=category,
            min_gti_score=min_gti_score,
            min_combined_score=min_combined_score
        )
        
        return {
            "task_type": "category_scan",
            "parameters": task.parameters, 
            "scan_result": result,
            "execution_time": (task.completed_at - task.started_at).total_seconds() if task.completed_at and task.started_at else None
        }
    
    def _execute_custom_scan(self, task: Task) -> Dict[str, Any]:
        """Thực thi custom list scan"""
        stocks_str = task.parameters.get("stocks", "")
        stock_list = [s.strip().upper() for s in stocks_str.split(",") if s.strip()]
        
        task.progress_message = f"Đang quét {len(stock_list)} mã cổ phiếu..."
        
        min_gti_score = task.parameters.get("min_gti_score", 2)
        min_combined_score = task.parameters.get("min_combined_score", 3)
        
        result = market_scan_parallel(
            stock_list=stock_list,
            min_gti_score=min_gti_score,
            min_combined_score=min_combined_score
        )
        
        return {
            "task_type": "custom_scan",
            "parameters": task.parameters,
            "scan_result": result,
            "execution_time": (task.completed_at - task.started_at).total_seconds() if task.completed_at and task.started_at else None
        }
    
    def _cleanup_expired_tasks(self):
        """
        Cleanup expired tasks (older than 1 hour)
        """
        current_time = datetime.now()
        expired_threshold = timedelta(hours=1)
        
        with self.lock:
            expired_task_ids = [
                task_id for task_id, task in self.tasks.items()
                if current_time - task.created_at > expired_threshold
            ]
            
            for task_id in expired_task_ids:
                del self.tasks[task_id]
        
        if expired_task_ids:
            print(f"Cleaned up {len(expired_task_ids)} expired tasks")
        
        # Schedule next cleanup
        self.cleanup_timer = threading.Timer(1800, self._cleanup_expired_tasks)
        self.cleanup_timer.daemon = True
        self.cleanup_timer.start()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê về task manager
        """
        with self.lock:
            total_tasks = len(self.tasks)
            status_counts = {}
            
            for status in TaskStatus:
                status_counts[status.value] = sum(
                    1 for task in self.tasks.values() 
                    if task.status == status
                )
        
        return {
            "total_tasks": total_tasks,
            "status_breakdown": status_counts,
            "executor_info": {
                "max_workers": self.executor._max_workers,
                "active_threads": self.executor._threads
            }
        }

# Global task manager instance
task_manager = TaskManager() 