import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import logo from '../designs/logo.png';

const navStyles = {
  container: {
    position: 'fixed',
    top: 10,
    right: 10,
    zIndex: 1000,
    paddingBottom: '90px',
    fontFamily: 'Helvetica, Arial, sans-serif',
  },
  iconContainer: {
    position: 'relative',
    width: 120,           
    height: 90,           
  },
  icon: {
    width: 70,
    height: 70,
    borderRadius: '50%',
    backgroundColor: 'transparent',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    overflow: 'hidden',
    boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
  },
  logoImg: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
  dropdown: {
    position: 'absolute',
    top: 80,
    right: 0,
    backgroundColor: '#fff',
    borderRadius: '8px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
    display: 'flex',
    flexDirection: 'column',
    border: '2px solid #003366',
    width: 180,
    overflow: 'hidden',
  },
  dropdownItem: {
    padding: '12px 24px',
    color: '#003366',
    textDecoration: 'none',
    cursor: 'pointer',
    fontWeight: 'bold',
    borderBottom: '1px solid #003366',
    transition: 'background-color 0.2s',
  },
  dropdownItemHover: {
    backgroundColor: '#cce5ff',
  },
};

const NavMenu = () => {
  const [hover, setHover] = useState(false);
  const [activeItem, setActiveItem] = useState(null);
  const navigate = useNavigate();

  const handleIconClick = () => {
    navigate('/');
  };

  return (
    <div style={navStyles.container}>
      <div
        style={navStyles.iconContainer}
        onMouseEnter={() => setHover(true)} 
        onMouseLeave={() => setHover(false)}  
      >
        <div style={navStyles.icon} onClick={handleIconClick}>
          <img src={logo} alt="Custom Logo" style={navStyles.logoImg} />
        </div>
        {hover && (
          <div style={navStyles.dropdown}>
            <div
              style={{
                ...navStyles.dropdownItem,
                ...(activeItem === 0 ? navStyles.dropdownItemHover : {}),
              }}
              onMouseEnter={() => setActiveItem(0)}
              onMouseLeave={() => setActiveItem(null)}
              onClick={() => navigate('/')}
            >
              Home
            </div>
            <div
              style={{
                ...navStyles.dropdownItem,
                ...(activeItem === 2 ? navStyles.dropdownItemHover : {}),
              }}
              onMouseEnter={() => setActiveItem(2)}
              onMouseLeave={() => setActiveItem(null)}
              onClick={() => navigate('/file-conversion')}
            >
              LIMS Converter
            </div>
            <div
              style={{
                ...navStyles.dropdownItem,
                ...(activeItem === 1 ? navStyles.dropdownItemHover : {}),
              }}
              onMouseEnter={() => setActiveItem(1)}
              onMouseLeave={() => setActiveItem(null)}
              onClick={() => navigate('/file-analysis')}
            >
              Quality Check
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NavMenu;
