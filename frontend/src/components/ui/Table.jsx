import React from 'react';

/**
 * Reusable Table Component with Tailwind CSS
 * 
 * @param {Array} columns - Array of column definitions: [{ key, header, render }]
 * @param {Array} data - Array of data rows
 * @param {function} onRowClick - Optional row click handler
 * @param {string} className - Additional custom classes
 */
const Table = ({ 
  columns = [], 
  data = [], 
  onRowClick,
  className = '',
  ...props 
}) => {
  return (
    <div className={`overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-md ${className}`}>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse table-fixed" {...props}>
          <thead>
            <tr className="bg-gradient-header border-b-2 border-gray-200">
              {columns.map((column, index) => (
                <th
                  key={column.key || index}
                  className="px-4 py-4 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider overflow-hidden text-ellipsis whitespace-nowrap"
                  style={column.width ? { width: column.width } : {}}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr>
                <td 
                  colSpan={columns.length} 
                  className="px-4 py-12 text-center text-gray-500"
                >
                  <div className="flex flex-col items-center gap-2">
                    <span className="text-4xl">📋</span>
                    <p>No data available</p>
                  </div>
                </td>
              </tr>
            ) : (
              data.map((row, rowIndex) => (
                <tr
                  key={row.id || rowIndex}
                  onClick={() => onRowClick && onRowClick(row)}
                  className={`border-b border-gray-200 last:border-b-0 transition-colors duration-150 ${
                    onRowClick ? 'cursor-pointer hover:bg-gray-50' : ''
                  }`}
                >
                  {columns.map((column, colIndex) => (
                    <td
                      key={`${rowIndex}-${column.key || colIndex}`}
                      className="px-4 py-4 text-sm text-gray-700 align-middle overflow-hidden text-ellipsis whitespace-nowrap"
                    >
                      {column.render ? column.render(row, rowIndex) : row[column.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Table Cell Components for common patterns
export const TableCell = ({ children, className = '' }) => (
  <div className={`overflow-hidden text-ellipsis whitespace-nowrap ${className}`}>
    {children}
  </div>
);

export const TableCellBold = ({ children, className = '' }) => (
  <div className={`font-semibold text-gray-900 overflow-hidden text-ellipsis whitespace-nowrap ${className}`}>
    {children}
  </div>
);

export const TableCellActions = ({ children, className = '' }) => (
  <div className={`flex items-center gap-2 flex-wrap ${className}`}>
    {children}
  </div>
);

export default Table;
