module C = Configurator.V1

let () =
  C.main ~name:"gtk4" (fun c ->
    let pkg_config = C.Pkg_config.get c in
      match pkg_config with
        | Some(pkg_config) ->
          let res = C.Pkg_config.query pkg_config ~package:"gtk4 gtk4-unix-print gio-unix-2.0" in
            (match res with
              | Some(flags) -> let () =C.Flags.write_sexp "gtk4-flags.sexp" flags.cflags in
                  C.Flags.write_sexp "gtk4-libs.sexp" flags.libs
              | None -> let () = print_endline("pkg-config could not find gtk4 gtk4-unix-print gio-unix-2.0") in exit 1 )

        | None -> let () = print_endline("pkg-config not found in path!") in exit 1
)