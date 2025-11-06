// Network Information Utility for Proctoring
class NetworkInfo {
    constructor() {
        this.ipAddress = null;
        this.macAddress = null;
        this.networkDetails = {};
    }

    // Get IP address using WebRTC
    async getIPAddress() {
        return new Promise((resolve) => {
            const pc = new RTCPeerConnection({
                iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
            });

            pc.createDataChannel('');
            pc.createOffer()
                .then(offer => pc.setLocalDescription(offer))
                .catch(() => resolve('Unknown'));

            pc.onicecandidate = (ice) => {
                if (!ice || !ice.candidate || !ice.candidate.candidate) return;
                
                const candidate = ice.candidate.candidate;
                const ipMatch = candidate.match(/([0-9]{1,3}(\.[0-9]{1,3}){3})/);
                
                if (ipMatch) {
                    const ip = ipMatch[1];
                    // Filter out local IPs
                    if (!ip.startsWith('127.') && !ip.startsWith('169.254.')) {
                        this.ipAddress = ip;
                        pc.close();
                        resolve(ip);
                    }
                }
            };

            // Fallback timeout
            setTimeout(() => {
                pc.close();
                resolve('Unknown');
            }, 3000);
        });
    }

    // Attempt to get MAC address (limited by browser security)
    async getMACAddress() {
        try {
            // Method 1: Try to get network interfaces (limited support)
            if (navigator.connection) {
                this.networkDetails.connectionType = navigator.connection.effectiveType;
                this.networkDetails.downlink = navigator.connection.downlink;
            }

            // Method 2: Generate a unique device fingerprint as MAC substitute
            const fingerprint = await this.generateDeviceFingerprint();
            this.macAddress = fingerprint;
            
            return fingerprint;
        } catch (error) {
            console.warn('MAC address detection failed:', error);
            return 'Unknown';
        }
    }

    // Generate device fingerprint as MAC address substitute
    async generateDeviceFingerprint() {
        const components = [];
        
        // Screen information
        components.push(screen.width + 'x' + screen.height);
        components.push(screen.colorDepth);
        
        // Timezone
        components.push(Intl.DateTimeFormat().resolvedOptions().timeZone);
        
        // Language
        components.push(navigator.language);
        
        // Platform
        components.push(navigator.platform);
        
        // User agent hash
        components.push(this.hashCode(navigator.userAgent));
        
        // Hardware concurrency
        components.push(navigator.hardwareConcurrency || 'unknown');
        
        // Memory (if available)
        if (navigator.deviceMemory) {
            components.push(navigator.deviceMemory);
        }
        
        // Canvas fingerprint
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillText('Device fingerprint', 2, 2);
            components.push(this.hashCode(canvas.toDataURL()));
        } catch (e) {
            components.push('canvas-error');
        }
        
        // WebGL fingerprint
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (gl) {
                const renderer = gl.getParameter(gl.RENDERER);
                const vendor = gl.getParameter(gl.VENDOR);
                components.push(this.hashCode(renderer + vendor));
            }
        } catch (e) {
            components.push('webgl-error');
        }
        
        const fingerprint = this.hashCode(components.join('|'));
        
        // Format as MAC-like address
        const hex = Math.abs(fingerprint).toString(16).padStart(12, '0').slice(0, 12);
        return hex.match(/.{2}/g).join(':').toUpperCase();
    }

    // Simple hash function
    hashCode(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return hash;
    }

    // Get all network information
    async getAllNetworkInfo() {
        const [ip, mac] = await Promise.all([
            this.getIPAddress(),
            this.getMACAddress()
        ]);

        return {
            ipAddress: ip,
            macAddress: mac,
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            connection: this.networkDetails
        };
    }

    // Get network info for proctoring
    async getProctoringNetworkInfo() {
        const info = await this.getAllNetworkInfo();
        return {
            ip_address: info.ipAddress,
            mac_address: info.macAddress
        };
    }
}

// Global instance
window.networkInfo = new NetworkInfo();

// Helper function for easy access
window.getNetworkInfo = async function() {
    return await window.networkInfo.getProctoringNetworkInfo();
};