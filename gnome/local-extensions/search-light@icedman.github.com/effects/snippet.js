'use strict';

import Cogl from 'gi://Cogl';

// GNOME 51 removed Clutter.ShaderEffect.set_shader_source; effects now hand Clutter a Cogl
// snippet from vfunc_get_static_snippet instead (see the Shell's own ui/lightbox.js). This turns
// one of our full fragment shaders into such a snippet: everything before main() becomes the
// declarations, and main()'s body replaces the default fragment code.
export const snippetFromShaderSource = (source) => {
  const main = source ? source.search(/void\s+main\s*\(\s*\)\s*\{/) : -1;
  if (main < 0) return Cogl.Snippet.new(Cogl.SnippetHook.FRAGMENT, null, null);

  const declarations = source.slice(0, main);
  const body = source.slice(source.indexOf('{', main) + 1, source.lastIndexOf('}'));
  const snippet = Cogl.Snippet.new(Cogl.SnippetHook.FRAGMENT, declarations, null);
  snippet.set_replace(body);
  return snippet;
};
