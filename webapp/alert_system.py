"""
Real-Time Alert System for Threat Detection
Manages alerts, notifications, and threat history
"""

import time
from datetime import datetime
from typing import Dict, List
from collections import deque

class AlertSystem:
    """
    Comprehensive alert system for maritime threat detection
    """
    
    # Alert severity levels
    SEVERITY_LEVELS = {
        'CRITICAL': {'priority': 4, 'color': '#dc2626', 'sound': 'critical'},
        'HIGH': {'priority': 3, 'color': '#ea580c', 'sound': 'high'},
        'MEDIUM': {'priority': 2, 'color': '#f59e0b', 'sound': 'medium'},
        'LOW': {'priority': 1, 'color': '#10b981', 'sound': 'low'}
    }
    
    # Threat type to severity mapping
    THREAT_SEVERITY_MAP = {
        'submarine': 'CRITICAL',
        'missile': 'CRITICAL',
        'human_diver': 'HIGH',
        'shark': 'HIGH',
        'monster': 'MEDIUM',
        'vessel': 'MEDIUM',
        'debris': 'LOW'
    }
    
    def __init__(self, max_history=100, alert_threshold=0.5):
        """
        Initialize alert system
        
        Args:
            max_history: Maximum number of alerts to keep in history
            alert_threshold: Minimum confidence to trigger alert
        """
        self.max_history = max_history
        self.alert_threshold = alert_threshold
        self.alert_history = deque(maxlen=max_history)
        self.active_alerts = {}
        self.alert_counter = 0
        
        # Statistics
        self.stats = {
            'total_alerts': 0,
            'critical_alerts': 0,
            'high_alerts': 0,
            'medium_alerts': 0,
            'low_alerts': 0,
            'threats_by_type': {}
        }
    
    def create_alert(self, threat: Dict, video_id: str = None, frame_number: int = None) -> Dict:
        """
        Create a new alert from threat detection
        
        Args:
            threat: Threat detection dictionary with confidence, class, etc.
            video_id: Unique identifier for video/image
            frame_number: Frame number in video (if applicable)
            
        Returns:
            Alert dictionary
        """
        # Check if confidence meets threshold
        confidence = threat.get('confidence', 0.0)
        if confidence < self.alert_threshold:
            return None
        
        # Determine severity
        threat_type = threat.get('class', threat.get('threat_type', 'unknown'))
        severity = self.THREAT_SEVERITY_MAP.get(threat_type, 'MEDIUM')
        
        # Override severity if threat has explicit severity
        if 'severity' in threat:
            severity = threat['severity']
        
        # Create alert
        self.alert_counter += 1
        alert = {
            'alert_id': self.alert_counter,
            'timestamp': datetime.now().isoformat(),
            'threat_type': threat_type,
            'confidence': confidence,
            'severity': severity,
            'priority': self.SEVERITY_LEVELS[severity]['priority'],
            'bbox': threat.get('bbox', []),
            'center': threat.get('center', []),
            'video_id': video_id,
            'frame_number': frame_number,
            'status': 'active',
            'acknowledged': False,
            'distance': threat.get('distance', {}),
            'threat_score': threat.get('threat_score', 0),
            'characteristics': threat.get('characteristics', {}),
            'behavior': threat.get('behavior', {}),
            'tactical_response': threat.get('tactical_response', 'Monitor and assess')
        }
        
        # Add to history
        self.alert_history.append(alert)
        
        # Add to active alerts
        self.active_alerts[alert['alert_id']] = alert
        
        # Update statistics
        self.stats['total_alerts'] += 1
        severity_key = f"{severity.lower()}_alerts"
        if severity_key in self.stats:
            self.stats[severity_key] += 1
        
        if threat_type not in self.stats['threats_by_type']:
            self.stats['threats_by_type'][threat_type] = 0
        self.stats['threats_by_type'][threat_type] += 1
        
        return alert
    
    def acknowledge_alert(self, alert_id: int) -> bool:
        """
        Mark an alert as acknowledged
        
        Args:
            alert_id: ID of alert to acknowledge
            
        Returns:
            True if successful
        """
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id]['acknowledged'] = True
            self.active_alerts[alert_id]['acknowledged_at'] = datetime.now().isoformat()
            return True
        return False
    
    def dismiss_alert(self, alert_id: int) -> bool:
        """
        Dismiss an active alert
        
        Args:
            alert_id: ID of alert to dismiss
            
        Returns:
            True if successful
        """
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id]['status'] = 'dismissed'
            self.active_alerts[alert_id]['dismissed_at'] = datetime.now().isoformat()
            del self.active_alerts[alert_id]
            return True
        return False
    
    def get_active_alerts(self, severity: str = None) -> List[Dict]:
        """
        Get all active alerts, optionally filtered by severity
        
        Args:
            severity: Filter by severity level (CRITICAL, HIGH, MEDIUM, LOW)
            
        Returns:
            List of active alerts sorted by priority
        """
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        
        # Sort by priority (highest first) then timestamp
        alerts.sort(key=lambda x: (-x['priority'], x['timestamp']), reverse=True)
        
        return alerts
    
    def get_alert_history(self, limit: int = None, severity: str = None) -> List[Dict]:
        """
        Get alert history
        
        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity level
            
        Returns:
            List of historical alerts
        """
        history = list(self.alert_history)
        
        if severity:
            history = [a for a in history if a['severity'] == severity]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_alert_summary(self) -> Dict:
        """
        Get summary of alert statistics
        
        Returns:
            Dictionary with alert statistics
        """
        active_by_severity = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        }
        
        for alert in self.active_alerts.values():
            severity = alert['severity']
            active_by_severity[severity] += 1
        
        return {
            'total_alerts': self.stats['total_alerts'],
            'active_count': len(self.active_alerts),
            'critical_count': self.stats['critical_alerts'],
            'high_count': self.stats['high_alerts'],
            'medium_count': self.stats['medium_alerts'],
            'low_count': self.stats['low_alerts'],
            'active_by_severity': active_by_severity,
            'threats_by_type': self.stats['threats_by_type'],
            'most_common_threat': max(self.stats['threats_by_type'].items(), 
                                     key=lambda x: x[1])[0] if self.stats['threats_by_type'] else None
        }
    
    def clear_old_alerts(self, max_age_seconds: int = 3600):
        """
        Clear alerts older than specified age
        
        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour)
        """
        current_time = time.time()
        to_remove = []
        
        for alert_id, alert in self.active_alerts.items():
            alert_time = datetime.fromisoformat(alert['timestamp']).timestamp()
            if current_time - alert_time > max_age_seconds:
                to_remove.append(alert_id)
        
        for alert_id in to_remove:
            self.dismiss_alert(alert_id)
    
    def generate_alert_report(self) -> str:
        """
        Generate text report of current alert status
        
        Returns:
            Formatted alert report string
        """
        summary = self.get_alert_summary()
        active_alerts = self.get_active_alerts()
        
        report = []
        report.append("=" * 80)
        report.append("MARITIME SECURITY ALERT SYSTEM - STATUS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append(f"ALERT SUMMARY:")
        report.append(f"  Total Alerts (All Time): {summary['total_alerts']}")
        report.append(f"  Active Alerts: {summary['active_count']}")
        report.append(f"    - Critical: {summary['active_by_severity']['CRITICAL']}")
        report.append(f"    - High: {summary['active_by_severity']['HIGH']}")
        report.append(f"    - Medium: {summary['active_by_severity']['MEDIUM']}")
        report.append(f"    - Low: {summary['active_by_severity']['LOW']}")
        report.append("")
        
        if active_alerts:
            report.append("ACTIVE THREATS:")
            for idx, alert in enumerate(active_alerts, 1):
                report.append(f"\n  [{idx}] {alert['severity']} - {alert['threat_type'].upper()}")
                report.append(f"      Confidence: {alert['confidence']*100:.1f}%")
                report.append(f"      Timestamp: {alert['timestamp']}")
                if alert.get('distance', {}).get('distance_display'):
                    report.append(f"      Distance: {alert['distance']['distance_display']}")
                report.append(f"      Response: {alert['tactical_response']}")
        else:
            report.append("No active threats detected.")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


# Global alert system instance
_alert_system = None

def get_alert_system():
    """Get or create the global alert system instance"""
    global _alert_system
    if _alert_system is None:
        _alert_system = AlertSystem()
    return _alert_system
