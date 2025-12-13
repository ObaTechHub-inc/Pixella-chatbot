document.addEventListener("DOMContentLoaded", function () {
    // Mobile detection - disable problematic features on mobile
    const isMobile = window.innerWidth <= 768;
    const isDesktop = window.innerWidth >= 1024;

    // Theme toggle functionality
    const themeToggle = document.createElement("button");
    themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
    themeToggle.className = "theme-toggle";
    themeToggle.setAttribute("aria-label", "Toggle theme");
    themeToggle.title = "Toggle dark/light mode";

    // Insert theme toggle in navigation
    const navContainer = document.querySelector(".nav-container");
    if (navContainer) {
      navContainer.appendChild(themeToggle);
    }

    // Load saved theme or detect system preference
    const savedTheme = localStorage.getItem("theme");
    const systemPrefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)"
    ).matches;
    const initialTheme = savedTheme || (systemPrefersDark ? "dark" : "light");

    document.documentElement.setAttribute("data-theme", initialTheme);
    updateThemeIcon(initialTheme);

    themeToggle.addEventListener("click", function () {
      const currentTheme = document.documentElement.getAttribute("data-theme");
      const newTheme = currentTheme === "dark" ? "light" : "dark";

      document.documentElement.setAttribute("data-theme", newTheme);
      localStorage.setItem("theme", newTheme);
      updateThemeIcon(newTheme);
    });

    function updateThemeIcon(theme) {
      themeToggle.innerHTML =
        theme === "dark"
          ? '<i class="fas fa-sun"></i>'
          : '<i class="fas fa-moon"></i>';
    }

    // Navigation toggle functionality
    const navToggle = document.querySelector(".nav-toggle");
    const navLinks = document.querySelector(".nav-links");

    if (navToggle && navLinks) {
      navToggle.addEventListener("click", function () {
        const expanded = navToggle.getAttribute("aria-expanded") === "true";
        navToggle.setAttribute("aria-expanded", !expanded);
        navLinks.classList.toggle("open");
        navToggle.classList.toggle("active");
      });

      // Close menu when clicking on a link
      navLinks.addEventListener("click", function (e) {
        if (e.target.tagName === "A") {
          navLinks.classList.remove("open");
          navToggle.classList.remove("active");
          navToggle.setAttribute("aria-expanded", "false");
        }
      });

      // Close menu when clicking outside
      document.addEventListener("click", function (e) {
        if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
          navLinks.classList.remove("open");
          navToggle.classList.remove("active");
          navToggle.setAttribute("aria-expanded", "false");
        }
      });
    }

    // Active navigation highlighting
    const currentPath = window.location.pathname;
    const navLinksArray = document.querySelectorAll(".nav-links a");

    navLinksArray.forEach((link) => {
      const linkPath = link.getAttribute("href");
      if (
        linkPath &&
        (currentPath === linkPath ||
          currentPath === linkPath.replace(".html", "") ||
          currentPath.endsWith(linkPath))
      ) {
        link.classList.add("active");
      }
    });

    // Documentation sidebar functionality
    const sidebarToggle = document.querySelector(".docs-sidebar-toggle");
    const sidebar = document.querySelector(".docs-sidebar");

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", function () {
            sidebar.classList.toggle("open");
            const expanded = sidebar.classList.contains("open");
            this.setAttribute("aria-expanded", expanded);
        });

        document.addEventListener("click", function (e) {
            if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                if (sidebar.classList.contains("open")) {
                    sidebar.classList.remove("open");
                    sidebarToggle.setAttribute("aria-expanded", "false");
                }
            }
        });
    }

    // Active navigation highlighting for sidebar
    const sidebarLinks = document.querySelectorAll(".docs-sidebar a");
    sidebarLinks.forEach((link) => {
    const linkPath = link.getAttribute("href");
    if (
        linkPath &&
        (currentPath === linkPath ||
        currentPath === linkPath.replace(".html", "") ||
        currentPath.endsWith(linkPath))
    ) {
        link.classList.add("active");
    }
    });


    // Auto-generate table of contents (disabled on mobile)
    if (!isMobile) {
      generateSidebarTOC();
    }

    // Initialize code copying (essential for mobile)
    initializeCodeCopying();
  });

  // Table of contents generation for sidebar
  function generateSidebarTOC() {
    const content = document.querySelector(".main-content");
    const sidebarToc = document.getElementById("sidebar-toc");

    if (!content || !sidebarToc) return;

    const headings = content.querySelectorAll("h1, h2, h3, h4, h5, h6");
    const lists = content.querySelectorAll("ul, ol");

    if (headings.length < 1 && lists.length < 1) {
      sidebarToc.innerHTML =
        '<p class="no-toc">No table of contents available</p>';
      return;
    }

    // Generate sidebar TOC items
    const tocList = document.createElement("ul");
    tocList.className = "toc-list";

    // Add headings to TOC
    headings.forEach((heading, index) => {
      const level = parseInt(heading.tagName.charAt(1));
      const id = heading.id || `heading-${index}`;
      heading.id = id;

      const listItem = document.createElement("li");
      listItem.className = `toc-item toc-h${level}`;
      listItem.innerHTML = `<a href="#${id}" class="toc-link">${heading.textContent}</a>`;

      tocList.appendChild(listItem);
    });

    // Add lists to TOC if they have meaningful content
    lists.forEach((list, index) => {
      const listItems = list.querySelectorAll("li");
      if (listItems.length > 0 && listItems.length <= 10) {
        // Only include reasonable-sized lists
        const listId = `list-${index}`;
        list.id = listId;

        // Get a preview of the list content
        const firstItem = listItems[0].textContent.substring(0, 30);
        const listType =
          list.tagName.toLowerCase() === "ol" ? "numbered" : "bulleted";
        const listTitle = `${listType} list: ${firstItem}${
          firstItem.length >= 30 ? "..." : ""
        }`;

        const listItem = document.createElement("li");
        listItem.className = "toc-item toc-list";
        listItem.innerHTML = `<a href="#${listId}" class="toc-link">${listTitle}</a>`;

        tocList.appendChild(listItem);
      }
    });

    sidebarToc.innerHTML = "";
    sidebarToc.appendChild(tocList);

    // Update active TOC item on scroll
    updateActiveTOCItem();
  }

  function updateActiveTOCItem() {
    const headings = document.querySelectorAll(
      ".main-content h1, .main-content h2, .main-content h3, .main-content h4, .main-content h5, .main-content h6"
    );
    const tocLinks = document.querySelectorAll(".sidebar-toc a");

    function updateActive() {
      let current = "";
      headings.forEach((heading) => {
        const rect = heading.getBoundingClientRect();
        if (rect.top <= 100) {
          current = heading.id;
        }
      });

      tocLinks.forEach((link) => {
        link.classList.remove("active");
        if (link.getAttribute("href") === `#${current}`) {
          link.classList.add("active");
        }
      });
    }

    window.addEventListener("scroll", updateActive);
    updateActive(); // Initial call
  }

  // Code copying functionality
  function initializeCodeCopying() {
    // Handle code blocks (pre elements)
    const codeBlocks = document.querySelectorAll("pre");
    codeBlocks.forEach((block) => {
      // Skip if already wrapped
      if (block.closest(".code-block-wrapper")) return;

      const wrapper = document.createElement("div");
      wrapper.className = "code-block-wrapper";

      const copyButton = document.createElement("button");
      copyButton.className = "code-copy-btn";
      copyButton.innerHTML = '<i class="fas fa-copy"></i>';
      copyButton.title = "Copy code";
      copyButton.setAttribute("aria-label", "Copy code block");

      copyButton.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        const code = block.querySelector("code") || block;
        copyToClipboard(code.textContent.trim());
        showCopyFeedback(this);
      });

      block.parentNode.insertBefore(wrapper, block);
      wrapper.appendChild(block);
      wrapper.appendChild(copyButton);
    });

    // Handle inline code (code elements not inside pre)
    const inlineCodes = document.querySelectorAll("code");
    inlineCodes.forEach((code) => {
      if (code.closest("pre")) return; // Skip code inside pre blocks

      code.style.cursor = "pointer";
      code.title = "Click to copy";

      code.addEventListener("click", function () {
        copyToClipboard(this.textContent.trim());
        showCopyFeedback(this);
      });
    });
  }

  function copyToClipboard(text) {
    navigator.clipboard.writeText(text).catch((err) => {
      // Fallback for older browsers
      const textArea = document.createElement("textarea");
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
    });
  }

  function showCopyFeedback(element) {
    const originalText = element.innerHTML;
    element.innerHTML = '<i class="fas fa-check"></i>';
    element.style.color = "#4CAF50";

    setTimeout(() => {
      element.innerHTML = originalText;
      element.style.color = "";
    }, 2000);
  }
