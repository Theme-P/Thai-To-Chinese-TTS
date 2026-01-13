document.addEventListener('DOMContentLoaded', () => {
    initSpeedSlider();
});

// Initialize speed slider
function initSpeedSlider() {
    const slider = document.getElementById('speed-slider');
    const display = document.getElementById('speed-display');

    slider.addEventListener('input', () => {
        display.textContent = `${slider.value}x`;
    });
}

// Handle conversion process
async function convert() {
    const thaiText = document.getElementById('thai-input').value.trim();
    const speed = document.getElementById('speed-slider').value;
    const btn = document.getElementById('convert-btn');
    const btnText = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.loader');
    const resultSection = document.getElementById('result-section');

    // Validation
    if (!thaiText) {
        alert('Please enter some Thai text.');
        return;
    }

    // UI Loading State
    btn.disabled = true;
    btnText.textContent = 'กำลังประมวลผล...';
    loader.classList.remove('hidden');
    resultSection.classList.add('hidden');

    try {
        const response = await fetch('/api/convert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: thaiText,
                speed: parseFloat(speed)
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Conversion failed');
        }

        // Display Results
        document.getElementById('chinese-output').textContent = data.chinese;
        document.getElementById('translator-info').textContent = `Translated via ${data.translator}`;
        document.getElementById('tts-info').textContent = `TTS: ${data.tts_engine}`;

        const audioPlayer = document.getElementById('audio-player');
        audioPlayer.src = data.audio_url;
        audioPlayer.load();

        // Update download link with correct format
        const downloadLink = document.getElementById('download-link');
        const fileExtension = data.audio_format || 'mp3'; // Default to mp3
        downloadLink.href = data.audio_url;
        downloadLink.download = `tts_output_${new Date().getTime()}.${fileExtension}`;
        downloadLink.classList.remove('hidden');

        // Show result section with smooth animation
        resultSection.classList.remove('hidden');

        // Auto play audio (optional)
        try {
            await audioPlayer.play();
        } catch (e) {
            console.log("Auto-play blocked, user must click play.");
        }

    } catch (error) {
        alert(error.message);
    } finally {
        // Reset UI State
        btn.disabled = false;
        btnText.textContent = 'แปลงเป็นเสียง';
        loader.classList.add('hidden');
    }
}
