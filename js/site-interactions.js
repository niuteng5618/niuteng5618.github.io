(function () {
  function ready(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  ready(function () {
    var rightRail = document.getElementById('rightRail');
    var railCollapseButton = document.getElementById('railCollapseButton');
    if (rightRail && railCollapseButton) {
      railCollapseButton.addEventListener('click', function () {
        rightRail.classList.toggle('collapsed');
        var collapsed = rightRail.classList.contains('collapsed');
        railCollapseButton.textContent = collapsed ? '⇤' : '⇥';
        railCollapseButton.setAttribute('aria-label', collapsed ? '展开博客目录' : '收起博客目录');
      });
    }

    var activeDirectoryItem = document.querySelector('.right-rail .blog-directory li.active');
    if (activeDirectoryItem) {
      var parentDetails = activeDirectoryItem.closest('.blog-directory-shell');
      if (parentDetails) parentDetails.open = true;
      var details = activeDirectoryItem.parentElement;
      while (details) {
        if (details.tagName === 'DETAILS') {
          details.open = true;
        }
        details = details.parentElement;
      }

      window.requestAnimationFrame(function () {
        activeDirectoryItem.scrollIntoView({ block: 'center', behavior: 'smooth' });
      });
    }

    var backToTop = document.getElementById('backToTop');
    if (backToTop) {
      var toggleBackToTop = function () {
        if (window.scrollY > 360) {
          backToTop.classList.add('visible');
        } else {
          backToTop.classList.remove('visible');
        }
      };

      backToTop.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });

      window.addEventListener('scroll', toggleBackToTop, { passive: true });
      toggleBackToTop();
    }

    var lightbox = document.getElementById('imageLightbox');
    var lightboxImg = document.getElementById('imageLightboxImg');
    var lightboxClose = document.getElementById('imageLightboxClose');
    if (lightbox && lightboxImg) {
      var closeLightbox = function () {
        lightbox.classList.remove('visible');
        lightbox.setAttribute('aria-hidden', 'true');
        lightboxImg.removeAttribute('src');
      };

      Array.prototype.slice.call(document.querySelectorAll('.entry img')).forEach(function (img) {
        img.classList.add('zoomable-image');
        img.addEventListener('click', function () {
          lightboxImg.src = img.src;
          lightboxImg.alt = img.alt || '图片预览';
          lightbox.classList.add('visible');
          lightbox.setAttribute('aria-hidden', 'false');
        });
      });

      if (lightboxClose) {
        lightboxClose.addEventListener('click', closeLightbox);
      }

      lightbox.addEventListener('click', function (event) {
        if (event.target === lightbox) {
          closeLightbox();
        }
      });

      document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
          closeLightbox();
        }
      });
    }

    var tagSearch = document.getElementById('tagSearch');
    if (tagSearch) {
      var tagCards = Array.prototype.slice.call(document.querySelectorAll('.tags-page .tag-cloud li'));
      var tagGroups = Array.prototype.slice.call(document.querySelectorAll('.tags-page .tag-group'));

      tagSearch.addEventListener('input', function () {
        var keyword = tagSearch.value.trim().toLowerCase();

        tagCards.forEach(function (item) {
          var text = item.textContent.toLowerCase();
          item.style.display = !keyword || text.indexOf(keyword) >= 0 ? '' : 'none';
        });

        tagGroups.forEach(function (group) {
          var text = group.textContent.toLowerCase();
          group.style.display = !keyword || text.indexOf(keyword) >= 0 ? '' : 'none';
        });
      });
    }
  });
})();
