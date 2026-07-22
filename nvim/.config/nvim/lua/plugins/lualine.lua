return {
  "nvim-lualine/lualine.nvim",
  opts = {
    options = {
      theme = "tokyonight",
      component_separators = "",
      section_separators = "",
      globalstatus = true,
    },
  },
  config = function()
    -- Custom transparent TokyoNight theme for lualine
    local colors = require("tokyonight.colors").setup({ transform = false })
    local tokyonight = {
      normal = {
        a = { fg = colors.blue, bg = "NONE" },
        b = { fg = colors.fg_gutter, bg = "NONE" },
        c = { fg = colors.fg, bg = "NONE" },
      },
      insert = {
        a = { fg = colors.green, bg = "NONE" },
        b = { fg = colors.fg_gutter, bg = "NONE" },
        c = { fg = colors.fg, bg = "NONE" },
      },
      visual = {
        a = { fg = colors.magenta, bg = "NONE" },
        b = { fg = colors.fg_gutter, bg = "NONE" },
        c = { fg = colors.fg, bg = "NONE" },
      },
      replace = {
        a = { fg = colors.red, bg = "NONE" },
        b = { fg = colors.fg_gutter, bg = "NONE" },
        c = { fg = colors.fg, bg = "NONE" },
      },
      command = {
        a = { fg = colors.yellow, bg = "NONE" },
        b = { fg = colors.fg_gutter, bg = "NONE" },
        c = { fg = colors.fg, bg = "NONE" },
      },
      inactive = {
        a = { fg = colors.comment, bg = "NONE" },
        b = { fg = colors.comment, bg = "NONE" },
        c = { fg = colors.comment, bg = "NONE" },
      },
    }
    require("lualine").setup({
      options = { theme = tokyonight },
    })
  end,
}
