SELECT
Fixed_Asset.[No_] AS Fixed_AssetNo_,
Fixed_Asset.[FA Class Code] AS Fixed_AssetFAClassCode,
Fixed_Asset.[FA Subclass Code] AS Fixed_AssetFASubclassCode,
Fixed_Asset.[FA Location Code] AS Fixed_AssetFALocationCode,
Fixed_Asset.[Vendor No_] AS Fixed_AssetVendorNo_,
Fixed_Asset.[Serial No_] AS Fixed_AssetSerialNo_,
Fixed_Asset.[FA Posting Group] AS Fixed_AssetFAPostingGroup,
Fixed_Asset.[FA Location Code Current] AS Fixed_AssetFALocationCodeCurrent,
Fixed_Asset.[Item No_] AS Fixed_AssetItemNo_,
Fixed_Asset.[MFG Serial Number] AS Fixed_AssetMFGSerialNumber,
Fixed_Asset.[State] AS Fixed_AssetState,
Fixed_Asset.[Service Item No_] AS Fixed_AssetServiceItemNo_,
Fixed_Asset.[PO No_] AS Fixed_AssetPONo_,
Fixed_Asset.[New Location] AS Fixed_AssetNewLocation,
Fixed_Asset.[Full Description] AS Fixed_AssetFullDescription,
Fixed_Asset.[Description] AS Fixed_AssetDescription,
FA_Depreciation_Book.[FA No_] AS FA_Depreciation_BookFANo_,
(
CASE
FA_Depreciation_Book.[Depreciation Method]
WHEN 0 THEN 'Straight-Line'
WHEN 1 THEN 'Declining-Balance 1'
WHEN 2 THEN 'Declining-Balance 2'
WHEN 3 THEN 'DB1/SL'
WHEN 4 THEN 'DB2/SL'
WHEN 5 THEN 'User-Defined'
WHEN 6 THEN 'Manual'
ELSE ''
END
) AS FA_Depreciation_BookDepreciationMethod,
CAST (
FA_Depreciation_Book.[No_ of Depreciation Years] AS Decimal (38, 10)
) AS FA_Depreciation_BookNo_ofDepreciationYears,

FA_Depreciation_Book.[Acquisition Date] AS FA_Depreciation_BookAcquisitionDate,
FA_Depreciation_Book.[Depreciation Starting Date] AS FA_Depreciation_BookDepreciationStartingDate,
FA_Depreciation_Book.[Depreciation Ending Date] AS FA_Depreciation_BookDepreciationEndingDate,
FA_Depreciation_Book.[Disposal Date] AS FA_Depreciation_BookDisposalDate,
FA_Depreciation_Book.[Depreciation Book Code] AS FA_Depreciation_BookDepreciationBookCode,
Service_Item.[No_] AS Service_ItemNo_,
Service_Item.[Serial No_] AS Service_ItemSerialNo_,
Service_Item.[Sales Order No_] AS Service_ItemSalesOrderNo_,
CAST (
(
SELECT
Sum([Amount])
FROM
[Multimedia Games, Inc_$FA Ledger Entry]
WHERE
(([FA No_] = [FA_Depreciation_Book].[FA No_]))
AND (
[Depreciation Book Code] = [FA_Depreciation_Book].[Depreciation Book Code]
)
AND ([FA Posting Category] = '')
AND ([FA Posting Type] = '0')
) AS Decimal (38, 10)
) AS FA_Depreciation_BookAcquisitionCost,

CAST (
(
  SELECT
    Sum([Amount])
  FROM
    [Multimedia Games, Inc_$FA Ledger Entry]
  WHERE
    ([FA No_] = [FA_Depreciation_Book].[FA No_])
    AND (
      [Depreciation Book Code] = [FA_Depreciation_Book].[Depreciation Book Code]
    )
    AND ([FA Posting Category] = '')
    AND ([FA Posting Type] = '1')
  ) AS Decimal (38, 10)
) AS FA_Depreciation_BookDepreciation,
CAST (
(
  SELECT
    Sum([Amount])
  FROM
    [Multimedia Games, Inc_$FA Ledger Entry]
  WHERE
    ([FA No_] = [FA_Depreciation_Book].[FA No_])
    AND (
      [Depreciation Book Code] = [FA_Depreciation_Book].[Depreciation Book Code]
    )
    AND ([Part of Book Value] = '1')
) AS Decimal (38, 10)
) AS FA_Depreciation_BookBookValue
FROM
  [Multimedia Games, Inc_$FA Depreciation Book] AS FA_Depreciation_Book FULL
  OUTER JOIN [Multimedia Games, Inc_$Fixed Asset] AS Fixed_Asset ON Fixed_Asset.[No_] = FA_Depreciation_Book.[FA No_]
  LEFT OUTER JOIN [Multimedia Games, Inc_$Service Item] AS Service_Item ON Service_Item.[No_] = Fixed_Asset.[Service Item No_]
