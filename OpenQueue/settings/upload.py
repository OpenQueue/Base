# -*- coding: utf-8 -*-


class B2Settings:
    def __init__(self, key_id: str, application_key: str,
                 bucket_id: str, cdn_url: str,
                 *args, **kwargs) -> None:
        """B2 Settings.

        Parameters
        ----------
        key_id: str
            B2 key ID.
        application_key: str
            B2 app key.
        bucket_id: str
            Bucket to upload to.
        cdn_url: str
            URL to access files.
        """

        super().__init__(*args, **kwargs)

        self.key_id = key_id
        self.application_key = application_key
        self.bucket_id = bucket_id
        self.cdn_url = cdn_url if cdn_url[-1:] == "/" else cdn_url + "/"


class DemoSettings:
    def __init__(self, compressed_extension: str = ".zip",
                 extension: str = ".dem",
                 pathway: str = "demos") -> None:
        """Demo settings.

        Parameters
        ----------
        compressed_extension : str, optional
            by default ".dem.zip"
        extension : str, optional
            by default ".dem"
        pathway : str, optional
            by default "demos"
        """

        self.compressed_extension = compressed_extension
        self.extension = extension

        if pathway[-1:] == "/":
            pathway = pathway[:-1]

        if pathway[0] == "/":
            pathway = pathway[1:]

        self.pathway = pathway


class PfpSettings:
    def __init__(self, pathway: str = "pfp") -> None:
        """Used to store PFP.

        Parameters
        ----------
        pathway : str
        """

        if pathway[-1:] == "/":
            pathway = pathway[:-1]

        if pathway[0] == "/":
            pathway = pathway[1:]

        self.pathway = pathway
