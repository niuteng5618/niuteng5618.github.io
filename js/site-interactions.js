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

    // 右侧栏的左右折叠：按钮独立于 rail，收起/展开过程可见且始终可点击
    if (rightRail && railCollapseButton) {
      railCollapseButton.addEventListener('click', function () {
        var collapsed = rightRail.classList.toggle('collapsed');
        document.body.classList.toggle('rail-collapsed', collapsed);
        railCollapseButton.textContent = collapsed ? '展开' : '收起';
        railCollapseButton.setAttribute('aria-label', collapsed ? '展开侧栏目录' : '收起侧栏目录');
      });
    }

    // 左侧博客信息区（头像 / 站名 / 导航）的折叠：状态记入 localStorage，刷新后保持
    var sidebarCollapseButton = document.getElementById('sidebarCollapseButton');
    if (sidebarCollapseButton) {
      var applySidebarState = function (collapsed) {
        document.body.classList.toggle('sidebar-collapsed', collapsed);
        sidebarCollapseButton.textContent = collapsed ? '展开' : '收起';
        sidebarCollapseButton.setAttribute('aria-label', collapsed ? '展开博客信息' : '收起博客信息');
      };

      if (window.localStorage && localStorage.getItem('sidebar-collapsed') === '1') {
        applySidebarState(true);
      }

      sidebarCollapseButton.addEventListener('click', function () {
        var collapsed = !document.body.classList.contains('sidebar-collapsed');
        applySidebarState(collapsed);
        try {
          localStorage.setItem('sidebar-collapsed', collapsed ? '1' : '0');
        } catch (e) {
          // 隐私模式下 localStorage 可能不可用，忽略即可
        }
      });
    }

    // 进入文档后：展开当前文章所在的目录链路，并滚动定位到当前文章
    // （文章页目录在左侧信息区，其他页面在右栏）
    var activeItem = document.querySelector('.blog-directory li.active');
    if (activeItem) {
      var node = activeItem.parentElement;
      while (node && node !== document.body) {
        if (node.tagName === 'DETAILS') {
          node.open = true;
        }
        node = node.parentElement;
      }

      window.requestAnimationFrame(function () {
        var container = activeItem.closest
          ? (activeItem.closest('.sidebar-directory') || rightRail)
          : rightRail;
        if (!container) {
          return;
        }
        var containerRect = container.getBoundingClientRect();
        var itemRect = activeItem.getBoundingClientRect();
        var delta = (itemRect.top - containerRect.top) - (container.clientHeight - itemRect.height) / 2;
        container.scrollTop += delta;
      });
    }

    // 右栏本文目录：滚动跟随高亮当前章节，并保持高亮项在栏内可见
    var postTocNav = document.getElementById('postTocNav');
    if (postTocNav) {
      var tocLinks = Array.prototype.slice.call(postTocNav.querySelectorAll('a[href^="#"]'));
      var tocTargets = tocLinks.map(function (link) {
        var raw = (link.getAttribute('href') || '').slice(1);
        var target = raw ? document.getElementById(raw) : null;
        if (!target && raw) {
          try {
            target = document.getElementById(decodeURIComponent(raw));
          } catch (e) {
            target = null;
          }
        }
        return target;
      });

      var activeTocLink = null;
      var highlightTocLink = function (link) {
        if (link === activeTocLink) {
          return;
        }
        if (activeTocLink) {
          activeTocLink.classList.remove('active');
        }
        activeTocLink = link;
        if (!link || !rightRail) {
          return;
        }
        link.classList.add('active');

        var railRect = rightRail.getBoundingClientRect();
        var linkRect = link.getBoundingClientRect();
        var linkTop = linkRect.top - railRect.top;
        if (linkTop < 40 || linkTop > rightRail.clientHeight - 40) {
          rightRail.scrollTop += (linkTop + linkRect.height / 2) - rightRail.clientHeight / 2;
        }
      };

      var updateTocSpy = function () {
        var current = null;
        for (var i = 0; i < tocTargets.length; i++) {
          if (tocTargets[i] && tocTargets[i].getBoundingClientRect().top <= 100) {
            current = tocLinks[i];
          }
        }
        // 滚动到页面底部时，高亮最后一项
        if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) {
          current = tocLinks.length ? tocLinks[tocLinks.length - 1] : null;
        }
        highlightTocLink(current);
      };

      window.addEventListener('scroll', function () {
        window.requestAnimationFrame(updateTocSpy);
      }, { passive: true });
      updateTocSpy();
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

    // 本文目录（正文卡片 + 右栏）：点击标题平滑跳转到对应正文，并让目标标题闪一下
    var tocCardLinks = document.querySelectorAll('.post-toc-card a, #postTocNav a');
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
