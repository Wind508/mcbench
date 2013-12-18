mcbench
-------

This is a small application that performs XPath queries against Matlab
code (ASTs that have been serialized to XML). This is useful to e.g.
analyze usage of certain Matlab features.

This [Matlab file exchange scraper][scraper] can be used to download Matlab
code from the Matlab Central File Exchange, and tools from the
[the McLab project][mclab] can be used to parse the code and serialize
the resulting ASTs to XML. The scraper also outputs a manifest with metadata
about each downloaded project; this is used to populate a SQLite database
that serves as an index.

An instance of this application is running at http://mcbench.cs.mcgill.ca.

[scraper]: https://github.com/isbadawi/matlab-file-exchange-scraper
[mclab]: https://github.com/Sable/mclab
