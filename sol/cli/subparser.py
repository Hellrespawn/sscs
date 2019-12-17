import argparse


class AccumulatingSubparserAction(argparse._SubParsersAction):
    def __call__(self, parser, namespace, values, option_string=None):
        _ = lambda x: x
        parser_name = values[0]
        arg_strings = values[1:]

        # set the parser name if requested
        if self.dest is not argparse.SUPPRESS:
            setattr(namespace, self.dest, parser_name)

        # select the parser
        try:
            parser = self._name_parser_map[parser_name]
        except KeyError:
            args = {
                "parser_name": parser_name,
                "choices": ", ".join(self._name_parser_map),
            }
            msg = (
                _("unknown parser %(parser_name)r (choices: %(choices)s)")
                % args
            )
            raise argparse.ArgumentError(self, msg)

        # parse all the remaining options into the namespace
        # store any unrecognized options on the object, so that the top
        # level parser can decide what to do with them

        # In case this subparser defines new defaults, we parse them
        # in a new namespace object and then update the original
        # namespace for the relevant parts.
        subnamespace, arg_strings = parser.parse_known_args(arg_strings, None)
        for key, value in vars(subnamespace).items():
            try:
                current = getattr(namespace, key)
                if isinstance(current, bool) and isinstance(value, bool):
                    setattr(namespace, key, current or value)

                elif isinstance(current, int) and isinstance(value, int):
                    setattr(namespace, key, current + value)

                else:
                    raise TypeError(
                        f"Trying to clobber existing option {key} with "
                        f"wrong type {type(current)} (expected {type(value)}!"
                    )

            except AttributeError:
                setattr(namespace, key, value)

        if arg_strings:
            vars(namespace).setdefault(argparse._UNRECOGNIZED_ARGS_ATTR, [])
            getattr(namespace, argparse._UNRECOGNIZED_ARGS_ATTR).extend(
                arg_strings
            )
