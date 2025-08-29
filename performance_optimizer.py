#!/usr/bin/env python3

import time
import psutil
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from threading import Lock
import queue
import multiprocessing


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    start_time: float
    end_time: Optional[float] = None
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    records_processed: int = 0
    throughput_per_sec: float = 0.0
    peak_memory_mb: float = 0.0


class PerformanceOptimizer:
    """Optimizes performance for Apple Health data processing."""
    
    def __init__(self):
        self.metrics = []
        self.peak_memory = 0.0
        self.current_metrics = None
        self.lock = Lock()
    
    def start_monitoring(self, operation_name: str) -> PerformanceMetrics:
        """Start performance monitoring for an operation."""
        with self.lock:
            self.current_metrics = PerformanceMetrics(
                start_time=time.time(),
                memory_usage_mb=self._get_memory_usage(),
                cpu_percent=psutil.cpu_percent()
            )
            logging.info(f"Started performance monitoring for: {operation_name}")
            return self.current_metrics
    
    def update_progress(self, records_processed: int) -> None:
        """Update progress and calculate throughput."""
        if not self.current_metrics:
            return
        
        with self.lock:
            self.current_metrics.records_processed = records_processed
            
            # Update memory tracking
            current_memory = self._get_memory_usage()
            self.current_metrics.memory_usage_mb = current_memory
            self.current_metrics.peak_memory_mb = max(
                self.current_metrics.peak_memory_mb, current_memory
            )
            
            # Calculate throughput
            elapsed = time.time() - self.current_metrics.start_time
            if elapsed > 0:
                self.current_metrics.throughput_per_sec = records_processed / elapsed
    
    def finish_monitoring(self) -> PerformanceMetrics:
        """Finish monitoring and return final metrics."""
        if not self.current_metrics:
            return None
        
        with self.lock:
            self.current_metrics.end_time = time.time()
            self.metrics.append(self.current_metrics)
            
            duration = self.current_metrics.end_time - self.current_metrics.start_time
            logging.info(f"Performance monitoring completed:")
            logging.info(f"  Duration: {duration:.2f}s")
            logging.info(f"  Records processed: {self.current_metrics.records_processed}")
            logging.info(f"  Throughput: {self.current_metrics.throughput_per_sec:.1f} records/sec")
            logging.info(f"  Peak memory: {self.current_metrics.peak_memory_mb:.1f} MB")
            
            result = self.current_metrics
            self.current_metrics = None
            return result
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations based on metrics."""
        recommendations = []
        
        if not self.metrics:
            return ["No performance data available yet"]
        
        latest = self.metrics[-1]
        
        # Memory recommendations
        if latest.peak_memory_mb > 1000:
            recommendations.append(
                f"High memory usage ({latest.peak_memory_mb:.1f} MB). "
                "Consider using streaming mode or reducing batch size."
            )
        
        # Throughput recommendations
        if latest.throughput_per_sec < 1000:
            recommendations.append(
                f"Low throughput ({latest.throughput_per_sec:.1f} records/sec). "
                "Consider increasing batch size or using parallel processing."
            )
        
        # Duration recommendations
        if latest.end_time and latest.end_time - latest.start_time > 300:  # 5 minutes
            recommendations.append(
                "Long processing time detected. Consider using streaming mode "
                "or breaking large files into smaller chunks."
            )
        
        if not recommendations:
            recommendations.append("Performance is within acceptable parameters.")
        
        return recommendations


class OptimizedXMLProcessor:
    """Optimized XML processor for large Apple Health files."""
    
    def __init__(self, batch_size: int = 2000, num_workers: int = None):
        self.batch_size = batch_size
        self.num_workers = num_workers or min(multiprocessing.cpu_count(), 4)
        self.processed_count = 0
        self.error_count = 0
        
    def process_large_xml_streaming(self, file_path: str, processor_func, progress_callback=None):
        """Process large XML files in streaming mode with optimizations."""
        logging.info(f"Processing {file_path} in optimized streaming mode")
        
        # Use iterparse for memory-efficient parsing
        context = ET.iterparse(file_path, events=('start', 'end'))
        context = iter(context)
        
        # Get root element
        event, root = next(context)
        
        batch = []
        
        try:
            for event, element in context:
                if event == 'end' and element.tag in ['Record', 'Workout', 'ActivitySummary']:
                    batch.append(element)
                    
                    # Clear processed element to save memory
                    element.clear()
                    
                    # Process batch when full
                    if len(batch) >= self.batch_size:
                        self._process_batch(batch, processor_func)
                        batch = []
                        
                        if progress_callback:
                            progress_callback(self.processed_count)
                    
                    # Clear ancestors to prevent memory buildup
                    while element.getprevious() is not None:
                        del element.getparent()[0]
            
            # Process remaining batch
            if batch:
                self._process_batch(batch, processor_func)
                
        except Exception as e:
            logging.error(f"Error processing XML: {e}")
            raise
        finally:
            # Clear root to free memory
            root.clear()
    
    def _process_batch(self, elements: List[ET.Element], processor_func):
        """Process a batch of XML elements with error handling."""
        if self.num_workers > 1:
            self._process_batch_parallel(elements, processor_func)
        else:
            self._process_batch_sequential(elements, processor_func)
    
    def _process_batch_sequential(self, elements: List[ET.Element], processor_func):
        """Process batch sequentially."""
        for element in elements:
            try:
                result = processor_func(element)
                if result:
                    self.processed_count += 1
            except Exception as e:
                self.error_count += 1
                logging.warning(f"Error processing element: {e}")
    
    def _process_batch_parallel(self, elements: List[ET.Element], processor_func):
        """Process batch using parallel processing."""
        try:
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                futures = [executor.submit(processor_func, element) for element in elements]
                
                for future in futures:
                    try:
                        result = future.result(timeout=30)  # 30 second timeout
                        if result:
                            self.processed_count += 1
                    except Exception as e:
                        self.error_count += 1
                        logging.warning(f"Error in parallel processing: {e}")
                        
        except Exception as e:
            logging.error(f"Parallel processing failed: {e}")
            # Fallback to sequential processing
            self._process_batch_sequential(elements, processor_func)


class MemoryOptimizer:
    """Memory optimization utilities."""
    
    @staticmethod
    def estimate_memory_needs(file_path: str) -> Dict[str, Any]:
        """Estimate memory requirements for processing a file."""
        file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
        
        # Estimate based on file size and XML parsing overhead
        estimated_memory_mb = file_size_mb * 2.5  # Conservative estimate
        
        # Check available memory
        available_memory_mb = psutil.virtual_memory().available / (1024 * 1024)
        
        return {
            'file_size_mb': file_size_mb,
            'estimated_memory_mb': estimated_memory_mb,
            'available_memory_mb': available_memory_mb,
            'can_load_in_memory': estimated_memory_mb < (available_memory_mb * 0.7),
            'recommended_batch_size': max(100, int(available_memory_mb / estimated_memory_mb * 1000))
        }
    
    @staticmethod
    def get_optimal_batch_size(file_size_mb: float, available_memory_mb: float) -> int:
        """Calculate optimal batch size based on available memory."""
        if available_memory_mb < 500:
            return 100  # Very small batches for limited memory
        elif available_memory_mb < 1000:
            return 500  # Small batches
        elif available_memory_mb < 2000:
            return 1000  # Medium batches
        else:
            return min(2000, int(file_size_mb * 20))  # Large batches for plenty of memory


class DatabaseOptimizer:
    """Database connection and query optimization."""
    
    @staticmethod
    def optimize_influxdb_writes(batch_size: int = 1000, parallel_writes: bool = True) -> Dict[str, Any]:
        """Get optimized settings for InfluxDB writes."""
        return {
            'batch_size': batch_size,
            'parallel_writes': parallel_writes,
            'connection_pool_size': 5 if parallel_writes else 1,
            'retry_attempts': 3,
            'retry_delay': 1,
            'timeout_seconds': 30,
            'compression': True
        }
    
    @staticmethod
    def get_write_optimization_config(record_count: int, memory_mb: float) -> Dict[str, Any]:
        """Get write optimization configuration based on data size."""
        if record_count < 10000:
            # Small dataset - prioritize simplicity
            return {
                'batch_size': min(1000, record_count),
                'parallel_writes': False,
                'connection_pool_size': 1
            }
        elif record_count < 100000:
            # Medium dataset - balance performance and resource usage
            return {
                'batch_size': 2000,
                'parallel_writes': True,
                'connection_pool_size': 3
            }
        else:
            # Large dataset - maximize performance
            return {
                'batch_size': min(5000, int(memory_mb / 10)),
                'parallel_writes': True,
                'connection_pool_size': 5
            }


def benchmark_processing_methods(file_path: str) -> Dict[str, float]:
    """Benchmark different processing methods to find the best approach."""
    results = {}
    
    # Test sequential processing
    start_time = time.time()
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        record_count = len(root.findall('.//Record'))
        sequential_time = time.time() - start_time
        results['sequential_parse'] = sequential_time
        results['record_count'] = record_count
    except Exception as e:
        logging.error(f"Sequential parsing failed: {e}")
        results['sequential_parse'] = float('inf')
    
    # Test streaming processing
    start_time = time.time()
    try:
        processor = OptimizedXMLProcessor(batch_size=1000)
        
        def dummy_processor(element):
            return element.tag
        
        processor.process_large_xml_streaming(file_path, dummy_processor)
        streaming_time = time.time() - start_time
        results['streaming_parse'] = streaming_time
    except Exception as e:
        logging.error(f"Streaming parsing failed: {e}")
        results['streaming_parse'] = float('inf')
    
    # Recommend best method
    if results['streaming_parse'] < results['sequential_parse'] * 0.8:
        results['recommended'] = 'streaming'
    else:
        results['recommended'] = 'sequential'
    
    return results


if __name__ == '__main__':
    # Example usage
    optimizer = PerformanceOptimizer()
    
    # Start monitoring
    metrics = optimizer.start_monitoring("test_operation")
    
    # Simulate processing
    for i in range(1000):
        time.sleep(0.001)  # Simulate work
        optimizer.update_progress(i)
    
    # Finish monitoring
    final_metrics = optimizer.finish_monitoring()
    
    # Get recommendations
    recommendations = optimizer.get_optimization_recommendations()
    print("Recommendations:")
    for rec in recommendations:
        print(f"  - {rec}")