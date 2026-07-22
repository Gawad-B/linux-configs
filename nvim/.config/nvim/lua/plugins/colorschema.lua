return {
  {
    "folke/tokyonight.nvim",
    opts = {
      transparent = true,
      styles = {
        sidebars = "transparent",
        floats = "transparent",
      },
      on_highlights = function(hl, c)
        hl.StatusLine = { bg = "NONE" }
        hl.StatusLineNC = { bg = "NONE" }
        hl.WinBar = { bg = "NONE" }
        hl.WinBarNC = { bg = "NONE" }
        hl.TabLine = { bg = "NONE" }
        hl.TabLineFill = { bg = "NONE" }
        hl.TabLineSel = { bg = "NONE" }
      end,
    },
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "tokyonight",
    },
  },
}
