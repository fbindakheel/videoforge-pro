"""
batch_processor.py — Queue-based batch video processing for VideoForge Pro
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from app.core.presets import JobConfig
from app.core.video_processor import VideoProcessor, build_output_path
from app.core.ffmpeg_manager import VideoInfo


class JobStatus(Enum):
    PENDING   = auto()
    RUNNING   = auto()
    DONE      = auto()
    ERROR     = auto()
    CANCELLED = auto()


@dataclass
class BatchJob:
    """A single entry in the batch queue."""
    input_path: str
    info: Optional[VideoInfo] = None
    config: Optional[JobConfig] = None
    output_path: str = ""
    status: JobStatus = JobStatus.PENDING
    error_msg: str = ""
    output_size: int = 0   # bytes, filled after completion
    progress: float = 0.0


class BatchProcessor(QObject):
    """
    Manages a queue of video jobs, running them one at a time using
    VideoProcessor threads. Emits signals for UI updates.
    """

    job_started        = pyqtSignal(int)          # index
    job_progress       = pyqtSignal(int, float)   # index, 0–100
    job_log            = pyqtSignal(int, str)      # index, log line
    job_done           = pyqtSignal(int, str, str) # index, in_path, out_path
    job_error          = pyqtSignal(int, str, str) # index, in_path, error
    batch_done         = pyqtSignal()
    overall_progress   = pyqtSignal(float)         # 0–100

    def __init__(self, ffmpeg_path: str, parent=None):
        super().__init__(parent)
        self.ffmpeg_path = ffmpeg_path
        self._jobs: list[BatchJob] = []
        self._current_index: int = -1
        self._current_worker: Optional[VideoProcessor] = None
        self._running = False

    # ── Job Management ────────────────────────────────────────────────────────

    def add_job(self, job: BatchJob) -> int:
        """Add a job to the queue. Returns its index."""
        self._jobs.append(job)
        return len(self._jobs) - 1

    def remove_job(self, index: int):
        """Remove a pending job by index (cannot remove running jobs)."""
        if 0 <= index < len(self._jobs):
            if self._jobs[index].status == JobStatus.PENDING:
                self._jobs.pop(index)

    def clear_pending(self):
        self._jobs = [j for j in self._jobs if j.status != JobStatus.PENDING]

    def clear_all(self):
        self.stop()
        self._jobs.clear()
        self._current_index = -1

    @property
    def jobs(self) -> list[BatchJob]:
        return self._jobs

    @property
    def is_running(self) -> bool:
        return self._running

    # ── Control ───────────────────────────────────────────────────────────────

    def start(self, shared_config: JobConfig):
        """
        Start processing the queue. Applies shared_config as the base
        config for all pending jobs.
        """
        if self._running:
            return
        self._running = True
        # Apply the shared settings to pending jobs
        for job in self._jobs:
            if job.status == JobStatus.PENDING:
                cfg = JobConfig(**shared_config.__dict__.copy())
                cfg.input_path = job.input_path
                cfg.output_path = build_output_path(cfg, job.input_path)
                job.config = cfg
                job.output_path = cfg.output_path
        self._process_next()

    def stop(self):
        """Cancel current job and stop the queue."""
        self._running = False
        if self._current_worker:
            self._current_worker.cancel()

    def _process_next(self):
        """Find and start the next pending job."""
        if not self._running:
            return

        next_index = None
        for i, job in enumerate(self._jobs):
            if job.status == JobStatus.PENDING:
                next_index = i
                break

        if next_index is None:
            self._running = False
            self.batch_done.emit()
            return

        self._current_index = next_index
        job = self._jobs[next_index]
        job.status = JobStatus.RUNNING
        self.job_started.emit(next_index)

        duration = job.info.duration if job.info else 0.0
        worker = VideoProcessor(job.config, self.ffmpeg_path, duration)
        self._current_worker = worker

        worker.progress.connect(lambda pct, idx=next_index: self._on_progress(idx, pct))
        worker.log.connect(lambda line, idx=next_index: self.job_log.emit(idx, line))
        worker.finished.connect(lambda inp, out, idx=next_index: self._on_done(idx, inp, out))
        worker.error.connect(lambda inp, err, idx=next_index: self._on_error(idx, inp, err))

        worker.start()

    def _on_progress(self, index: int, pct: float):
        if 0 <= index < len(self._jobs):
            self._jobs[index].progress = pct
        self.job_progress.emit(index, pct)
        self._emit_overall_progress()

    def _on_done(self, index: int, input_path: str, output_path: str):
        import os
        job = self._jobs[index]
        job.status = JobStatus.DONE
        job.progress = 100.0
        try:
            job.output_size = os.path.getsize(output_path)
        except Exception:
            job.output_size = 0
        self.job_done.emit(index, input_path, output_path)
        self._emit_overall_progress()
        self._process_next()

    def _on_error(self, index: int, input_path: str, error: str):
        job = self._jobs[index]
        if self._running:
            job.status = JobStatus.ERROR
        else:
            job.status = JobStatus.CANCELLED
        job.error_msg = error
        self.job_error.emit(index, input_path, error)
        self._process_next()

    def _emit_overall_progress(self):
        total = len(self._jobs)
        if total == 0:
            return
        done = sum(1 for j in self._jobs if j.status in (JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED))
        running_pct = 0.0
        for j in self._jobs:
            if j.status == JobStatus.RUNNING:
                running_pct = j.progress
                break
        overall = ((done * 100) + running_pct) / total
        self.overall_progress.emit(overall)

    # ── Statistics ────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        total = len(self._jobs)
        done = sum(1 for j in self._jobs if j.status == JobStatus.DONE)
        errors = sum(1 for j in self._jobs if j.status == JobStatus.ERROR)
        input_bytes = sum(j.info.file_size for j in self._jobs if j.info)
        output_bytes = sum(j.output_size for j in self._jobs if j.status == JobStatus.DONE)
        saved = max(0, input_bytes - output_bytes)
        return {
            "total": total,
            "done": done,
            "errors": errors,
            "saved_bytes": saved,
        }
