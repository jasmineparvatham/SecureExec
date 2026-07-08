class VerificationReport:
    def __init__(self, program_name="unknown"):
        self.program_name = program_name
        self.passed = True
        self.errors = []
        self.warnings = []
        self.security_score = 100
        
        self.resource_risk = "LOW"
        self.detected_loops = 0
        self.bounded_loops = 0
        self.estimated_iterations = 0
        self.rejection_reason = None
        self.rejection_details = {}

    def add_error(self, message):
        self.errors.append(message)
        self.passed = False
        self.security_score -= 20
        self.resource_risk = "HIGH"

    def add_warning(self, message):
        self.warnings.append(message)
        self.security_score -= 5

    def format_report(self):
        status = "PASSED" if self.passed else "REJECTED"
        score = max(0, self.security_score)
        
        report = []
        report.append("--------------------------------")
        report.append("SecureExec Verification Report")
        report.append(f"Program: {self.program_name}")
        report.append(f"Status: {status}")
        report.append("")
        
        report.append("Checks:")
        if not self.errors:
            report.append("✓ Instruction validity")
            report.append("✓ Register initialization")
            report.append("✓ Memory safety")
            report.append("✓ Resource limits")
        else:
            report.append("✗ Instruction validity")
        report.append("")
        
        report.append(f"Security Score: {score}/100")
        report.append("")
        
        report.append("Resource Risk:")
        report.append(self.resource_risk)
        report.append("")
        
        report.append("Loop Analysis:")
        report.append("Detected loops:")
        report.append(str(self.detected_loops))
        report.append("")
        report.append("Bounded loops:")
        report.append(str(self.bounded_loops))
        report.append("")
        report.append("Estimated maximum iterations:")
        report.append(str(self.estimated_iterations))
        report.append("")
        
        if self.rejection_reason:
            report.append("Reason:")
            report.append(self.rejection_reason)
            report.append("")
            if getattr(self, "rejection_analysis", None):
                report.append("Analysis:")
                report.append(self.rejection_analysis)
                report.append("")
            if self.rejection_details:
                report.append("Details:")
                for k, v in self.rejection_details.items():
                    report.append(f"{k}:")
                    report.append(str(v))
                    report.append("")
        elif self.errors:
            report.append("Errors:")
            for err in self.errors:
                report.append(f"✗ {err}")
            report.append("")
            
        if self.warnings:
            report.append("Warnings:")
            for warn in self.warnings:
                report.append(f"⚠ {warn}")
            report.append("")
            
        report.append("--------------------------------")
        return "\n".join(report)

    def __str__(self):
        return self.format_report()
