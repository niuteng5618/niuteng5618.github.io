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

    // 右侧目录的左右折叠：按钮独立于 rail，收起/展开过程可见且始终可点击
    if (rightRail && railCollapseButton) {
      railCollapseButton.addEventListener('click', function () {
        var collapsed = rightRail.classList.toggle('collapsed');
        document.body.classList.toggle('rail-collapsed', collapsed);
        railCollapseButton.textContent = collapsed ? '展开' : '收起';
        railCollapseButton.setAttribute('aria-label', collapsed ? '展开博客目录' : '收起博客目录');
      });
    }

    // 进入文档后：右栏目录展开当前文章所在链路，其余只显示到二级，并滚动定位到当前文章
    var activeItem = document.querySelector('.right-rail .blog-directory li.active');
    if (activeItem && rightRail) {
      var node = activeItem.parentElement;
      while (node && node !== rightRail) {
        if (node.tagName === 'DETAILS') {
          node.open = true;
        }
        node = node.parentElement;
      }

      window.requestAnimationFrame(function () {
        var railRect = rightRail.getBoundingClientRect();
        var itemRect = activeItem.getBoundingClientRect();
        var delta = (itemRect.top - railRect.top) - (rightRail.clientHeight - itemRect.height) / 2;
        rightRail.scrollTop += delta;
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

    // 本文目录卡片：点击标题平滑跳转到对应正文，并让目标标题闪一下
    var tocCardLinks = document.querySelectorAll('.post-toc-card a');
    if (tocCardLinks.length) {
      var flashTimer = null;
      var flashHeading = function (el) {
        if (!el) return;
        el.classList.remove('toc-flash');
        // 强制回流以便重复点击时动画能重新触发
        void el.offsetWidth;
        el.classList.add('toc-flash');
        if (flashTimer) {
          clearTimeout(flashTimer);
        }
        flashTimer = setTimeout(function () {
          el.classList.remove('toc-flash');
        }, 1500);
      };

      Array.prototype.slice.call(tocCardLinks).forEach(function (link) {
        link.addEventListener('click', function (event) {
          var href = link.getAttribute('href') || '';
          if (href.charAt(0) !== '#' || href.length < 2) {
            return;
          }
          var raw = href.slice(1);
          var target = document.getElementById(raw);
          if (!target) {
            try {
              target = document.getElementById(decodeURIComponent(raw));
            } catch (e) {
              target = null;
            }
          }
          if (target) {
            event.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            flashHeading(target);
            if (window.history && window.history.replaceState) {
              window.history.replaceState(null, '', href);
            }
          }
        });
      });
    }
  });
})();
