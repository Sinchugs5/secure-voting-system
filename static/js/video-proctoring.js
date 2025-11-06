class VideoProctoring {
    constructor() {
        this.stream = null;
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.isRecording = false;
        this.violations = [];
        this.faceDetectionInterval = null;
        this.tabSwitchCount = 0;
        this.startTime = Date.now();
    }

    async startProctoring() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 640, height: 480 }, 
                audio: true 
            });
            
            // Wait for video element to be available
            let attempts = 0;
            while (attempts < 10) {
                const videoElement = document.getElementById('proctoring-video');
                if (videoElement) {
                    videoElement.srcObject = this.stream;
                    videoElement.play();
                    break;
                }
                await new Promise(resolve => setTimeout(resolve, 100));
                attempts++;
            }

            this.startRecording();
            this.startFaceDetection();
            this.setupTabSwitchDetection();
            this.setupFullscreenDetection();
            
            console.log('Video proctoring started');
            return true;
        } catch (error) {
            console.error('Failed to start proctoring:', error);
            this.addViolation('Camera access denied');
            return false;
        }
    }

    startRecording() {
        this.mediaRecorder = new MediaRecorder(this.stream);
        this.recordedChunks = [];

        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.recordedChunks.push(event.data);
            }
        };

        this.mediaRecorder.start(5000); // Record in 5-second chunks
        this.isRecording = true;
    }

    startFaceDetection() {
        this.faceDetectionInterval = setInterval(() => {
            this.detectFace();
        }, 3000);
    }

    detectFace() {
        const video = document.getElementById('proctoring-video');
        if (!video) return;

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);

        // Simple face detection check (you can integrate with face-api.js for better detection)
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const brightness = this.calculateBrightness(imageData);
        
        if (brightness < 50) {
            this.addViolation('Poor lighting detected');
        }
    }

    calculateBrightness(imageData) {
        let sum = 0;
        const data = imageData.data;
        for (let i = 0; i < data.length; i += 4) {
            sum += (data[i] + data[i + 1] + data[i + 2]) / 3;
        }
        return sum / (data.length / 4);
    }

    setupTabSwitchDetection() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.tabSwitchCount++;
                this.addViolation(`Tab switched away (${this.tabSwitchCount} times)`);
            }
        });

        window.addEventListener('blur', () => {
            this.addViolation('Window lost focus');
        });
    }

    setupFullscreenDetection() {
        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement) {
                this.addViolation('Exited fullscreen mode');
            }
        });
    }

    addViolation(violation) {
        const timestamp = new Date().toISOString();
        this.violations.push({
            violation,
            timestamp,
            timeFromStart: Date.now() - this.startTime
        });
        
        console.warn('Proctoring violation:', violation);
        this.showViolationAlert(violation);
    }

    showViolationAlert(violation) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'proctoring-alert';
        alertDiv.innerHTML = `
            <div style="position: fixed; top: 20px; right: 20px; background: #ff4444; color: white; padding: 10px 15px; border-radius: 5px; z-index: 9999; font-size: 14px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
                ⚠️ ${violation}
            </div>
        `;
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }

    async stopProctoring() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
        }
        
        if (this.faceDetectionInterval) {
            clearInterval(this.faceDetectionInterval);
        }
        
        console.log('Video proctoring stopped');
        return this.generateReport();
    }

    generateReport() {
        const endTime = Date.now();
        const duration = endTime - this.startTime;
        
        return {
            duration: Math.round(duration / 1000), // in seconds
            violations: this.violations,
            tabSwitchCount: this.tabSwitchCount,
            totalViolations: this.violations.length,
            recordedChunks: this.recordedChunks.length
        };
    }

    async uploadRecording(voterUsername) {
        if (this.recordedChunks.length === 0) return null;

        const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
        const formData = new FormData();
        formData.append('recording', blob, `voting-session-${voterUsername}-${Date.now()}.webm`);
        formData.append('violations', JSON.stringify(this.violations));
        formData.append('username', voterUsername);
        
        // Add network information
        try {
            if (window.getNetworkInfo) {
                const networkInfo = await window.getNetworkInfo();
                formData.append('mac_address', networkInfo.mac_address);
                console.log('Network info captured:', networkInfo);
            } else {
                formData.append('mac_address', 'Network utility not loaded');
            }
        } catch (error) {
            console.warn('Failed to get network info:', error);
            formData.append('mac_address', 'Error capturing network info');
        }

        try {
            const response = await fetch('/upload-proctoring-data', {
                method: 'POST',
                body: formData
            });
            return await response.json();
        } catch (error) {
            console.error('Failed to upload recording:', error);
            return null;
        }
    }
}

// Global proctoring instance
window.videoProctoring = new VideoProctoring();