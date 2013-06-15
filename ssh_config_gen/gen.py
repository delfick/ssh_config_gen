import types

class BadTemplateException(Exception):
    """Raised when we have a bad template"""

def merge_options(*options):
    """Helper to merge multiple dictionaries into one"""
    new_options = {}
    for opts in options:
        if opts:
            new_options.update(opts)
    return new_options

class Section(object):
    """Knows how to generate an ssh config from specified options"""
    def __init__(self, options, name=""):
        self.name = name
        self.options = options

    def generate(self):
        """Yield the lines in the section"""
        banner = self.banner
        verbatim = self.verbatim

        if banner:
            yield banner

        if verbatim:
            yield verbatim

        for host in self.hosts:
            for lines in host.generate():
                yield lines

        for section in self.sections:
            for lines in section.generate():
                yield lines

    @property
    def banner(self):
        """If this section has a name, return it wrapped in a hash banner"""
        if not self.name:
            return None

        return '\n'.join(['#' * 25, "{}  {}".format('#' * 3, self.name.upper()), '#' * 25])

    @property
    def verbatim(self):
        """Return verbatim options for this section if any"""
        return self.options.get("verbatim", "").strip()

    @property
    def hosts(self):
        """Return hosts for this section if any"""
        for host, options in sorted(self.options.get("hosts", {}).items()):
            yield Host(host, self.update_options(options))

        for alias, host in sorted(self.options.get("simple", {}).items()):
            yield Host(host, self.update_options({'alias': alias}))

    @property
    def sections(self):
        """Return sections inside this section if any"""
        return [Section(self.update_options(options), name=name) for name, options in sorted(self.options.get("sections", {}).items())]

    def update_options(self, options):
        """Return options such that options['options'] has defaults from self.options['options']"""
        new_options = {}
        if options:
            new_options.update(options)
        else:
            options = {}
        new_options['options'] = merge_options(self.options.get('options'), options.get("options"))
        return new_options

class Host(object):
    """Represents a host"""
    def __init__(self, host, options):
        self.host = host
        self.options = options

    def generate(self):
        """Yield hosts as strings from the provided host and options"""
        for raw_host, host, options, proxying in self.spinoffs:
            new_options = merge_options(self.options.get('options'), options)
            if self.proxied_by and 'ProxyCommand' not in new_options:
                new_options['ProxyCommand'] = self.proxy_command(self.proxied_by)
            other_options = sorted((key, val) for key, val in new_options.items() if key != 'HostName')
            yield self.lines_for([("Host", host), ("HostName", new_options['HostName'])] + other_options)

            for proxied, options in proxying.items():
                proxied_options = merge_options(options)
                proxied_options['options'] = merge_options(new_options, proxied_options.get('options'), {'ProxyCommand': self.proxy_command(raw_host)})
                for lines in Host(proxied, proxied_options).generate():
                    yield lines

    @property
    def alias(self):
        """Return alias if we have one"""
        return self.options.get("alias")

    @property
    def proxied_by(self):
        """Return proxied_by if we have one"""
        return self.options.get("proxied_by")

    @property
    def count(self):
        """Return count if we have one"""
        return self.options.get("count")

    @property
    def count_start(self):
        """Return count_start if we have one"""
        return self.options.get("count_start", 1)

    @property
    def proxying(self):
        """Return (host, options) for anything this host is proxying"""
        return self.options.get("proxying", {})

    @property
    def formatting(self):
        """Yield (format, options) from formatting if there are any"""
        formatting = self.options.get("formatting", [])
        if not isinstance(formatting, types.ListType):
            raise BadTemplateException("Expected formatting to be a list of dictionaries. Not {}".format(formatting))

        if formatting:
            for nxt in formatting:
                yield [nxt.get(key, dflt) for key, dflt in
                    [('format_options', {}), ('options', {}), ('proxying', {}), ('alias', self.alias), ('count', self.count), ('count_start', self.count_start)]
                ]
        else:
            yield (None, {}, self.proxying, self.alias, self.count, self.count_start)

    @property
    def format_options(self):
        """Get any format options on this host"""
        return self.options.get('format_options', {})

    @property
    def spinoffs(self):
        """Yield (host, options) pairs that come from this host"""
        for format_options, options, proxying, alias, count, count_start in list(self.formatting):
            format_options = merge_options(self.format_options, format_options)

            if not count:
                count = 1
            for index in range(count):
                if format_options.get('count') != str(index + count_start):
                    format_options = self.adjust_format_counts(format_options)
                    format_options['count'] = str(index + count_start)

                host = self.host.format(**format_options)
                formatted_alias =alias
                if alias:
                    formatted_alias = alias.format(**format_options)

                # Setup the hostname and add any aliases
                raw_host = host
                options['HostName'] = raw_host
                if formatted_alias:
                    host = "{} {}".format(raw_host, formatted_alias)

                merged_proxying = {}
                for key, val in proxying.items():
                    merged_proxying[key] = merge_options(val)
                    merged_proxying[key]['format_options'] = merge_options(format_options, merged_proxying[key].get('format_options'))

                yield raw_host, host, options, merged_proxying

    def lines_for(self, items):
        """Return us lines for the (key, value) pairs in items"""
        lines = []
        for key, val in items:
            if val is True:
                val = 'yes'
            elif val is False:
                val = 'no'
            lines.append("{} {}".format(key, val))
        return '\n'.join(lines)

    def proxy_command(self, host):
        """Return a proxy command to this host"""
        return "ssh -q {} -W %h:%p".format(host)

    def adjust_format_counts(self, options):
        """Move around the count variables in the options"""
        counts = [(key[5:] or '0', val) for key, val in options.items() if str(key).startswith("count") and not str(key)[5:] or str(key)[5:].isdigit()]
        if 'count' in options:
            del options['count']

        for num, val in counts:
            options['count{}'.format(int(num)+1)] = val

        return options

