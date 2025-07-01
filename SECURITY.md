# Security Policy

## Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest| :x:                |

**Note**: As an actively developed project, we recommend always using the latest version from the `main` branch for the most up-to-date security patches.

## Security Philosophy

Mango Tango CLI is designed with security in mind:

- **Local-First**: All data processing occurs locally on your machine
- **No Remote Data Transmission**: Data never leaves your system unless explicitly exported
- **Minimal Dependencies**: We use a curated set of well-maintained dependencies
- **Input Validation**: All user inputs and data imports are validated
- **Secure Defaults**: Safe configuration defaults that prioritize security

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow responsible disclosure practices:

### 🔒 For Security-Sensitive Issues

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please email us directly at:
**[sandobenjamin@gmail.com](mailto:sandobenjamin@gmail.com)**

Include the following information:

- **Description**: Clear description of the vulnerability
- **Impact**: Potential impact and attack scenarios
- **Reproduction Steps**: Detailed steps to reproduce the issue
- **Environment**: Operating system, Python version, and Mango Tango CLI version
- **Proof of Concept**: Code or screenshots demonstrating the issue (if applicable)

### 📧 What to Expect

1. **Acknowledgment**: We'll acknowledge receipt within **48 hours**
2. **Initial Assessment**: Initial vulnerability assessment within **7 days**
3. **Regular Updates**: Progress updates every **7 days** until resolution
4. **Resolution Timeline**: We aim to resolve security issues within **30 days**
5. **Disclosure**: Coordinated disclosure after fix is deployed

### 🏆 Recognition

We believe in recognizing security researchers who help improve our project:

- **Security Credits**: Recognition in release notes and documentation
- **Hall of Fame**: Listed in our security contributors (with permission)

## Security Best Practices for Users

### Data Protection

- **Sensitive Data**: Be cautious when importing files containing personally identifiable information (PII)
- **File Permissions**: Ensure your data files have appropriate permissions
- **Workspace Security**: Keep your Mango Tango CLI workspace directory secure
- **Export Security**: Review exported data before sharing externally

### Environment Security

- **Virtual Environment**: Always use a virtual environment for isolation
- **Dependency Updates**: Keep dependencies updated by re-running bootstrap scripts
- **Python Version**: Use the supported Python 3.12 version
- **Source Verification**: Only download Mango Tango CLI from official sources

### Development Security

- **Code Review**: All contributions undergo security-focused code review
- **Dependency Scanning**: Dependencies are regularly audited for vulnerabilities
- **Static Analysis**: Code is analyzed for potential security issues
- **Secrets Management**: Never commit secrets, API keys, or sensitive data

## Common Security Considerations

### Data Import Risks

- **Malicious Files**: Be cautious with data files from untrusted sources
- **File Size Limits**: Large files may impact system performance
- **Data Validation**: All imported data is validated, but verify data integrity
- **Encoding Issues**: Files with unusual encodings are handled safely

### Web Dashboard Security

- **Local Servers**: Web dashboards run locally and are not exposed externally
- **Port Security**: Dashboard servers use local-only binding
- **Data Exposure**: Dashboards only display your own data
- **Cross-Origin**: CORS protections prevent unauthorized access

### Analysis Module Security

- **Code Execution**: Analysis modules run in controlled environments
- **Resource Limits**: Analyses have memory and processing limits
- **File Access**: Modules only access designated input/output paths
- **Sandbox**: Analysis execution is isolated from system resources

## Security Hardening

### For Development

```bash
# Verify checksums of dependencies
pip-audit

# Run security linting
bandit -r .

# Check for known vulnerabilities
safety check
```

### For Deployment

- Use virtual environments
- Limit file system permissions
- Monitor resource usage
- Regular dependency updates

## Vulnerability Disclosure Timeline

### Our Commitment

1. **0-2 days**: Acknowledge vulnerability report
2. **3-7 days**: Confirm and assess severity
3. **7-30 days**: Develop and test fix
4. **30+ days**: Deploy fix and coordinate disclosure

### Severity Classification

- **Critical**: Remote code execution, data exfiltration
- **High**: Local privilege escalation, data corruption
- **Medium**: Information disclosure, denial of service
- **Low**: Minor information leaks, configuration issues

## Security Features

### Current Security Measures

- **Input Sanitization**: All user inputs are validated and sanitized
- **Path Traversal Protection**: File operations are restricted to safe directories
- **Memory Safety**: Python's memory management prevents common buffer issues
- **Dependency Pinning**: Specific dependency versions prevent supply chain attacks
- **Local Processing**: No data transmitted to external services

### Planned Security Enhancements

- Enhanced input validation for complex data formats
- Additional sandboxing for analysis modules
- Automated security scanning in CI/CD pipeline
- Security-focused documentation and training materials

## Compliance and Standards

### Data Protection

- **GDPR Awareness**: Guidance for handling EU personal data
- **Data Minimization**: Process only necessary data
- **Purpose Limitation**: Use data only for stated analysis purposes
- **Retention Policies**: Recommendations for data lifecycle management

### Industry Standards

- Following OWASP guidelines for secure coding
- Adherence to Python security best practices
- Regular security audits and assessments

## Emergency Response

### Security Incident Response

In case of a confirmed security incident:

1. **Immediate**: Stop using affected functionality
2. **Report**: Email security team immediately
3. **Document**: Preserve evidence and logs
4. **Update**: Apply patches as soon as available
5. **Review**: Assess impact and improve processes

### Communication Channels

- **Emergency**: [sandobenjamin@gmail.com](mailto:sandobenjamin@gmail.com)
- **General**: GitHub Issues (for non-security bugs)
- **Community**: [Civic Tech DC Slack](https://civictechdc.slack.com)

## Security Resources

### External Resources

- [OWASP Python Security Guidelines](https://owasp.org/www-project-python-security/)
- [Python Security Documentation](https://docs.python.org/3/library/security_warnings.html)
- [Civic Tech DC Security Practices](https://civictechdc.org)

### Contact Information

- **Security Team**: [sandobenjamin@gmail.com](mailto:sandobenjamin@gmail.com)
- **Project Maintainers**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Organization**: [CIB Mango Tree](https://github.com/CIB-Mango-Tree)

---

**Last Updated**: July 2025

Thank you for helping keep Mango Tango CLI secure for everyone!
