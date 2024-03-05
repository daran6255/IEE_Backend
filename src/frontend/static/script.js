document.getElementById('fileInput').addEventListener('change', function(event) {
  const file = event.target.files[0];
  const imagePreview = document.getElementById('imagePreview');
  const browseLabel = document.getElementById('browseLabel');
  const closeImageBtn = document.getElementById('closeImageBtn');

  if (file && file.type === 'image/jpeg') {
      const reader = new FileReader();

      reader.onload = function(e) {
          const img = new Image();
          img.src = e.target.result;
          img.classList.add('preview-image');
          imagePreview.innerHTML = '';
          imagePreview.appendChild(img);
          browseLabel.style.display = 'none'; // Hide browse button
          closeImageBtn.style.display = 'block'; // Show close button
      }

      reader.readAsDataURL(file);
  }
});

document.getElementById('closeImageBtn').addEventListener('click', function() {
  const imagePreview = document.getElementById('imagePreview');
  const browseLabel = document.getElementById('browseLabel');
  const closeImageBtn = document.getElementById('closeImageBtn');

  imagePreview.innerHTML = ''; // Clear image preview
  browseLabel.style.display = 'block'; // Show browse button
  closeImageBtn.style.display = 'none'; // Hide close button
});
